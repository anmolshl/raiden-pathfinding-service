from gevent import monkey  # isort:skip # noqa
monkey.patch_all()  # isort:skip # noqa

import logging
import sys

import click
from raiden_libs.blockchain import BlockchainListener
from raiden_contracts.contract_manager import CONTRACT_MANAGER
from raiden_contracts.constants import (
    CONTRACT_TOKEN_NETWORK_REGISTRY,
    CONTRACT_TOKEN_NETWORK,
)
from web3 import HTTPProvider, Web3
from raiden_libs.no_ssl_patch import no_ssl_verification
from requests.exceptions import ConnectionError
from raiden_libs.test.mocks.dummy_transport import DummyTransport

from pathfinder.pathfinding_service import PathfindingService
from pathfinder.api.rest import NetworkInfoAPI

log = logging.getLogger(__name__)


@click.command()
@click.option(
    '--eth-rpc',
    default='http://localhost:8545',
    type=str,
    help='Ethereum node RPC URI'
)
def main(
    eth_rpc,
):
    # setup logging
    logging.basicConfig(level=logging.INFO)

    logging.getLogger('web3').setLevel(logging.INFO)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)

    log.info("Starting Raiden Metrics Server")

    try:
        log.info(f'Starting Web3 client for node at {eth_rpc}')
        web3 = Web3(HTTPProvider(eth_rpc))

    except ConnectionError as error:
        log.error(
            'Can not connect to the Ethereum client. Please check that it is running and that '
            'your settings are correct.'
        )
        sys.exit()

    with no_ssl_verification():
        service = None
        try:
            log.info('Starting TokenNetwork Listener...')
            token_network_listener = BlockchainListener(
                web3,
                CONTRACT_MANAGER,
                CONTRACT_TOKEN_NETWORK,
                sync_start_block=3_000_000,
            )

            log.info('Starting TokenNetworkRegistry Listener...')
            token_network_registry_listener = BlockchainListener(
                web3,
                CONTRACT_MANAGER,
                CONTRACT_TOKEN_NETWORK_REGISTRY,
                sync_start_block=3_000_000,
            )

            service = PathfindingService(
                CONTRACT_MANAGER,
                DummyTransport(),
                token_network_listener,
                chain_id=int(web3.net.version),
                token_network_registry_listener=token_network_registry_listener
            )

            api = NetworkInfoAPI(service)
            api.run(port=5678)

            print('Running... http://localhost:5678/info')
            service.run()

        except (KeyboardInterrupt, SystemExit):
            print('Exiting...')
        finally:
            if service:
                log.info('Stopping Raiden Metrics Server')
                service.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
