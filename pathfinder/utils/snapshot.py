# -*- coding: utf-8 -*-
from typing import Dict, List
import os
import pickle

from eth_utils import is_checksum_address, to_checksum_address

from pathfinder.token_network import TokenNetwork
from pathfinder.utils.types import Address

PFS_DIRECTORY = '.raiden-pfs'
FILE_ENDING = '.pfs-snapshot'


def base_path() -> str:
    return os.path.join(os.path.expanduser('~'), PFS_DIRECTORY)


def get_snapshot_path(address: Address, confirmed_block_number: int) -> str:
    """ Returns a snapshot path for the given address and block number. """
    return os.path.join(
        base_path(),
        to_checksum_address(address),
        f'block_{confirmed_block_number}{FILE_ENDING}'
    )


def get_available_snapshots(basepath: str) -> Dict[Address, List[str]]:
    """ Returns a mapping of token network addresses to snapshots. """
    result = {}
    for entry in os.scandir(basepath):
        if not entry.is_dir() or not is_checksum_address(entry.name):
            continue

        token_network_address = Address(entry.name)

        snapshots = []
        for possible_snapshot in os.scandir(os.path.join(basepath, token_network_address)):
            if not possible_snapshot.is_file() or not possible_snapshot.name.endswith(FILE_ENDING):
                continue

            snapshots.append(possible_snapshot.path)

        if len(snapshots) > 0:
            result[token_network_address] = sorted(snapshots)

    return result


def get_latest_snapshot(snapshots: List[str]) -> str:
    """ Returns the latest snapshot from a list of snapshot names. """
    # TODO: fixme
    sorted_snapshots = sorted(snapshots)
    return sorted_snapshots[-1]


def save_token_network_snapshot(path: str, token_network: TokenNetwork):
    """ Serializes the token network so it doesn't need to sync from scratch when
    the snapshot is loaded. """
    with open(path, 'wb') as f:
        data = dict(
            channel_id_to_addresses=token_network.channel_id_to_addresses,
            graph=token_network.G
        )
        pickle.dump(data, f, 4)


def update_token_network_from_snapshot(token_network: TokenNetwork, snapshot_path: str):
    """ Deserializes the token network so it doesn't need to sync from scratch """
    with open(snapshot_path, 'rb') as f:
        data = pickle.load(f)

        try:
            # try to load data first
            channel_id_to_addresses = data['channel_id_to_addresses']
            graph = data['graph']

            # then update, so it's not update partly
            token_network.channel_id_to_addresses = channel_id_to_addresses
            token_network.G = graph
        except KeyError:
            raise ValueError('Invalid snapshot')
