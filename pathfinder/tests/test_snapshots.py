# -*- coding: utf-8 -*-
import os

from eth_utils import to_checksum_address

from pathfinder.utils.types import Address
from pathfinder.utils.snapshot import (
    get_snapshot_path,
    get_available_snapshots,
    base_path,
    get_latest_snapshot
)


def touch_test_file(tmpdir_object, directory, filename):
    if tmpdir_object.join(directory).check():
        file = tmpdir_object.join(directory).join(filename)
    else:
        file = tmpdir_object.mkdir(directory).join(filename)
    file.write('test')


def test_snapshot_path():
    address = Address('a' * 40)

    path1 = get_snapshot_path(address, 1)
    assert path1 == os.path.join(
        base_path(),
        '0xaAaAaAaaAaAaAaaAaAAAAAAAAaaaAaAaAaaAaaAa/block_1.pfs-snapshot'
    )

    address_checksummed = to_checksum_address(address)
    path2 = get_snapshot_path(address_checksummed, 1)
    assert path1 == path2


def test_snapshot_listing(tmpdir):
    address1 = 'notanaddress'
    address2 = Address('a' * 40)
    address3 = to_checksum_address(address2)
    address4 = to_checksum_address('b' * 40)

    touch_test_file(tmpdir, address1, 'block_1.pfs-snapshot')
    touch_test_file(tmpdir, address2, 'block_1.pfs-snapshot')
    touch_test_file(tmpdir, address3, 'block_1.pfs-snapshot')
    touch_test_file(tmpdir, address3, 'block_1.tmp')
    touch_test_file(tmpdir, address4, 'block_1.pfs-snapshot')
    touch_test_file(tmpdir, address4, 'block_2.pfs-snapshot')

    print(tmpdir)

    listing = get_available_snapshots(tmpdir)
    assert listing == {
        '0xaAaAaAaaAaAaAaaAaAAAAAAAAaaaAaAaAaaAaaAa': [
            os.path.join(tmpdir, address3, 'block_1.pfs-snapshot')
        ],
        '0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB': [
            os.path.join(tmpdir, address4, 'block_1.pfs-snapshot'),
            os.path.join(tmpdir, address4, 'block_2.pfs-snapshot')
        ]
    }

    tmpdir.remove()


def test_get_latest_snapshot():
    snapshots = [
        '/path/to/snapshot/block_1.pfs-snapshot',
        '/path/to/snapshot/block_5.pfs-snapshot',
        '/path/to/snapshot/block_100.pfs-snapshot',
        '/path/to/snapshot/block_11.pfs-snapshot',
        '/path/to/snapshot/block_1000.pfs-snapshot',
        '/path/to/snapshot/block_50.pfs-snapshot',
        '/path/to/snapshot/block_111.pfs-snapshot',
    ]

    assert get_latest_snapshot(snapshots) == '/path/to/snapshot/block_1000.pfs-snapshot'
