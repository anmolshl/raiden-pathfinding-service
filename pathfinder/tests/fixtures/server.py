# -*- coding: utf-8 -*-
import pytest

from raiden_libs.blockchain import BlockchainListener


@pytest.fixture
def blockchain(web3, contract_manager):
    blockchain = BlockchainListener(
        web3,
        contract_manager,
        'TokenNetwork',
        poll_interval=1
    )
    return blockchain
