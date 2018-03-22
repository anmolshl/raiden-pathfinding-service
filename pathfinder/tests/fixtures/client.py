# -*- coding: utf-8 -*-
import random

import pytest
from eth_utils import denoms
from pathfinder.tests.mocks.client import MockRaidenNode


@pytest.fixture
def get_random_privkey():
    return lambda: "0x%064x" % random.randint(
        1,
        0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    )


@pytest.fixture
def generate_raiden_client(
    web3,
    ethereum_tester,
    token_network_contracts,
    token_contracts,
    faucet_address,
    get_random_privkey,
    contract_manager,
):
    """factory function to create a new Raiden client. The client has some funds
    allocated by default and has no open channels
    """
    def f():
        pk = get_random_privkey()
        token_network_contract = token_network_contracts[0]
        token_contract = token_contracts[0]
        c = MockRaidenNode(web3, pk, token_network_contract, contract_manager)
        token_contract.transact({'from': faucet_address}).transfer(
            c.address,
            10000
        )
        ethereum_tester.add_account(pk)
        c.token_contract = token_contract
        ethereum_tester.send_transaction({
            'from': faucet_address,
            'to': c.address,
            'gas': 21000,
            'value': 1 * denoms.ether
        })
        return c
    return f


@pytest.fixture
def generate_raiden_clients(
    generate_raiden_client
):
    def f(count=1):
        return [generate_raiden_client() for x in range(count)]
    return f
