from typing import Dict

from pathfinder.model import TokenNetwork


def token_network_to_dict(token_network: TokenNetwork) -> Dict:
    """ Return a JSON serialized version of the token network.

    {
        "token_address": "0xsomething",
        "num_nodes": 3,
        "num_channels": 4,
        "nodes": [
            "0xalbert",
            "0xberta",
            "0xceasar",
        ],
        "channels": [
            {
                "channel_identifier": "0xchannel",
                "status": "open",
                "participant1": "0xalbert",
                "participant2": "0xceasar",
                "deposit1": 100,
                "deposit2": 50,
                "withdraw1": 20,
                "withdraw2": 0,
            },
            ...
        ],
    }
    """
    channel_ids = token_network.channel_id_to_addresses.keys()

    participants = []
    channels = []
    for channel_id in channel_ids:
        ends = token_network.channel_id_to_addresses[channel_id]
        participants.extend(ends)

        p1, p2 = ends

        view1 = token_network.G[p1][p2]['view']
        view2 = token_network.G[p2][p1]['view']

        channel = dict(
            channel_identifier=channel_id,
            # state=view1.state,
            participant1=ends[0],
            participant2=ends[1],
            deposit1=view1.deposit,
            deposit2=view2.deposit,
            capacity1=view1.capacity,
            capacity2=view2.capacity,
        )

        channels.append(channel)

    # sets are not json serializable, convert back to list
    participants_deduped = list(set(participants))

    return dict(
        token_address=token_network.address,
        num_channels=len(channel_ids),
        num_nodes=len(participants_deduped),
        nodes=participants_deduped,
        channels=channels,
    )
