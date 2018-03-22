from eth_utils import is_checksum_address, is_same_address
from web3.utils.events import get_event_data

from raiden_libs.utils import private_key_to_address

NULL_ADDRESS = '0x0000000000000000000000000000000000000000'


class MockRaidenNode:
    def __init__(self, web3, privkey, channel_contract, contract_manager):
        self.privkey = privkey
        self.address = private_key_to_address(privkey)
        self.contract = channel_contract
        self.partner_to_channel_id = dict()
        self.token_network_abi = None
        self.token_contract = None
        self.web3 = web3
        self.contract_manager = contract_manager

    # @sync_channels
    def open_channel(self, partner_address):
        assert is_checksum_address(partner_address)
        # disallow multiple open channels with a same partner
        if partner_address in self.partner_to_channel_id:
            return self.partner_to_channel_id[partner_address]
        channel_address = NULL_ADDRESS
        if is_same_address(channel_address, NULL_ADDRESS):
            # if it doesn't exist, register new channel
            txid = self.contract.contract.transact({'from': self.address}).openChannel(
                self.address,
                partner_address,
                15
            )
            assert txid is not None
            tx = self.web3.eth.getTransactionReceipt(txid)
            assert tx is not None
            assert len(tx['logs']) == 1
            event = get_event_data(
                self.contract_manager.get_event_abi('TokenNetwork', 'ChannelOpened'),
                tx['logs'][0]
            )

        channel_id = event['args']['channel_identifier']
        assert channel_id > 0
        assert (is_same_address(event['args']['participant1'], self.address) or
                is_same_address(event['args']['participant2'], self.address))
        assert (is_same_address(event['args']['participant1'], partner_address) or
                is_same_address(event['args']['participant2'], partner_address))

        self.partner_to_channel_id[partner_address] = channel_id
        return channel_id
