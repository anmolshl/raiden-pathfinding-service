# -*- coding: utf-8 -*-
import logging
import sys
import traceback
from typing import Dict, Optional, List

import gevent
from web3 import Web3
from eth_utils import is_checksum_address
from raiden_libs.blockchain import BlockchainListener
from raiden_libs.gevent_error_handler import register_error_handler
from raiden_libs.transport import MatrixTransport
from raiden_contracts.contract_manager import ContractManager

from pathfinder.token_network import TokenNetwork
from pathfinder.utils.types import Address
from pathfinder.utils.snapshot import (
    base_path,
    get_available_snapshots,
    get_snapshot_path,
    get_latest_snapshot,
    save_token_network_snapshot,
    update_token_network_from_snapshot
)

log = logging.getLogger(__name__)


def error_handler(context, exc_info):
    log.fatal("Unhandled exception terminating the program")
    traceback.print_exception(
        etype=exc_info[0],
        value=exc_info[1],
        tb=exc_info[2]
    )
    sys.exit()


class PathfindingService(gevent.Greenlet):
    def __init__(
        self,
        web3: Web3,
        contract_manager: ContractManager,
        transport: MatrixTransport,
        token_network_listener: BlockchainListener,
        load_snapshots: bool = True,
        *,
        token_network_registry_listener: BlockchainListener = None,
        follow_networks: List[Address] = None,
    ) -> None:
        super().__init__()
        self.web3 = web3
        self.contract_manager = contract_manager
        self.transport = transport
        self.token_network_listener = token_network_listener

        self.token_network_registry_listener = token_network_registry_listener
        self.follow_networks = follow_networks

        self.is_running = gevent.event.Event()
        self.transport.add_message_callback(lambda message: self.on_message_event(message))
        self.token_networks: Dict[Address, TokenNetwork] = {}

        assert (
            self.follow_networks is not None or self.token_network_registry_listener is not None
        )
        self._setup_token_networks(load_snapshots)

        # subscribe to event notifications from blockchain listener
        self.token_network_listener.add_confirmed_listener(
            'ChannelOpened',
            self.handle_channel_opened
        )
        self.token_network_listener.add_confirmed_listener(
            'ChannelNewDeposit',
            self.handle_channel_new_deposit
        )
        self.token_network_listener.add_confirmed_listener(
            'ChannelClosed',
            self.handle_channel_closed
        )

    def _setup_token_networks(self, load_snapshots: bool):
        # load networks from snapshots
        if load_snapshots:
            self.load_snapshots(self.follow_networks)

        # TODO: only load snapshots that are desired
        if self.follow_networks:
            for network_address in self.follow_networks:
                self.create_token_network_for_address(network_address)
        else:
            self.token_network_registry_listener.add_confirmed_listener(
                'TokenNetworkCreated',
                self.handle_token_network_created
            )

    def _run(self):
        register_error_handler(error_handler)
        self.transport.start()
        self.token_network_listener.start()
        if self.token_network_registry_listener:
            self.token_network_registry_listener.start()

        self.is_running.wait()

    def stop(self):
        self.is_running.set()

    def on_message_event(self, message: str):
        """This handles messages received over the Transport"""
        # TODO: process messages
        print(message)

    def _get_token_network(self, event) -> Optional[TokenNetwork]:
        token_network_address = event['address']
        assert is_checksum_address(token_network_address)

        try:
            token_network = self.token_networks[token_network_address]
        except KeyError:
            log.info('Ignoring event from unknown token network {}'.format(
                token_network_address
            ))
            return None

        return token_network

    def handle_channel_opened(self, event):
        token_network = self._get_token_network(event)

        if token_network:
            log.debug('Received ChannelOpened event for token network {}'.format(
                token_network.address
            ))

            channel_identifier = event['args']['channel_identifier']
            participant1 = event['args']['participant1']
            participant2 = event['args']['participant2']

            token_network.handle_channel_opened(
                channel_identifier,
                participant1,
                participant2
            )

    def handle_channel_new_deposit(self, event):
        token_network = self._get_token_network(event)

        if token_network:
            log.debug('Received ChannelNewDeposit event for token network {}'.format(
                token_network.address
            ))

            channel_identifier = event['args']['channel_identifier']
            participant_address = event['args']['participant']
            total_deposit = event['args']['total_deposit']

            token_network.handle_channel_new_deposit_event(
                channel_identifier,
                participant_address,
                total_deposit
            )

    def handle_channel_closed(self, event):
        token_network = self._get_token_network(event)

        if token_network:
            log.debug('Received ChannelClosed event for token network {}'.format(
                token_network.address
            ))

            channel_identifier = event['args']['channel_identifier']

            token_network.handle_channel_closed_event(channel_identifier)

    def handle_token_network_created(self, event):
        # TODO: check that the address is our token network address
        token_network_address = event['args']['token_network_address']
        assert is_checksum_address(token_network_address)

        log.info(f'Found new token network at {token_network_address}')
        self.create_token_network_for_address(token_network_address)

    def create_token_network_for_address(self, token_network_address: Address) -> TokenNetwork:
        if token_network_address in self.token_networks.keys():
            return self.token_networks[token_network_address]
        else:
            log.info(f'Following token network at {token_network_address}')
            # TODO: check that no network is duplicated
            contract = self.web3.eth.contract(
                token_network_address,
                abi=self.contract_manager.get_contract_abi('TokenNetwork')
            )

            token_network = TokenNetwork(contract)
            self.token_networks[token_network_address] = token_network

            return token_network

    # FIXME: this need to be called
    def save_snapshots(self):
        """ Save the current token networks to snapshots. """
        for address, token_network in self.token_networks.items():
            path = get_snapshot_path(address, self.token_network_listener.confirmed_head_number)
            save_token_network_snapshot(path, token_network)

    def load_snapshots(self, follow_networks: List[Address] = None):
        """ Load token networks from available snapshots. """
        min_block = sys.maxsize
        for address, snapshot_paths in get_available_snapshots(base_path()).items():
            # skip if the address is not in follow networks
            if address not in follow_networks:
                continue

            latest_snapshot = get_latest_snapshot(snapshot_paths)

            token_network = self.create_token_network_for_address(address)
            try:
                min_block_snapshot = update_token_network_from_snapshot(
                    token_network,
                    latest_snapshot
                )

                min_block = min(min_block, min_block_snapshot)
            except ValueError:
                log.warn(
                    "Could not load snapshot '%s' for token network %s",
                    latest_snapshot,
                    address
                )

        self.token_network_listener.sync_start_block = min_block
        if self.token_network_registry_listener:
            self.token_network_registry_listener.sync_start_block = min_block
