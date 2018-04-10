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


def save_token_network_snapshot(path: str, token_network: TokenNetwork):
    """ Serializes the token network so it doesn't need to sync from scratch when
    the snapshot is loaded. """
    with open(path, 'wb') as f:
        pickle.dump(token_network, f, 4)


def load_token_network_from_snapshot(snapshot_path: str) -> TokenNetwork:
    """ Deserializes the token network so it doesn't need to sync from scratch """
    with open(snapshot_path, 'rb') as f:
        return pickle.load(f)
