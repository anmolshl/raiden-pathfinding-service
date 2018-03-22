# -*- coding: utf-8 -*-
import gevent


def test_open_event(
    generate_raiden_clients,
    blockchain,
    ethereum_tester,
):
    """Test opening, closing and settling the channel"""
    events_confirmed = []
    events_unconfirmed = []
    blockchain.add_confirmed_listener(
        'ChannelOpened',
        lambda e: events_confirmed.append(e)
    )
    blockchain.add_unconfirmed_listener(
        'ChannelOpened',
        lambda e: events_unconfirmed.append(e)
    )

    # start the blockchain listener
    blockchain.start()
    gevent.sleep()  # give the listener some time to start up

    c1, c2 = generate_raiden_clients(2)
    # open a channel
    c1.open_channel(c2.address)
    gevent.sleep(1)

    ethereum_tester.mine_block()
    gevent.sleep(1)  # poll interval is 1

    # the unconfirmed event should be received now
    assert len(events_unconfirmed) == 1

    ethereum_tester.mine_blocks(3)
    gevent.sleep(1)

    assert len(events_confirmed) > 0

    blockchain.stop()
