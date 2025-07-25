from cachetools import TTLCache, cached
from rapidfuzz import process
from slack_sdk import WebClient

from slack_mcp.models import MatchedContact, NamesMatchResponse


def get_all_channels(client: WebClient):
    channels = []
    cursor = None
    while True:
        response = client.conversations_list(
            types="im,mpim,public_channel,private_channel", limit=100000, cursor=cursor
        )
        channels.extend(response["channels"])
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return channels


def get_favourite_channel_ids(client: WebClient):
    favourites_response = client.stars_list()
    favourites = favourites_response.get("items", [])
    favourite_channel_ids = [x["channel"] for x in favourites]
    return favourite_channel_ids


def get_single_message(client: WebClient, channel_id: str, ts: str):
    res = client.conversations_history(
        channel=channel_id, oldest=ts, newest=ts, inclusive=True, limit=1
    )
    return res["messages"][0]


_channelid_to_name_cache = TTLCache(maxsize=8, ttl=300)


@cached(_channelid_to_name_cache)
def compute_channelid_to_name_cached(client: WebClient):
    return compute_channelid_to_name(client)


def compute_channelid_to_name(client: WebClient):
    channel_to_name = {}

    # Step 1: Get all users (one request)
    users_response = client.users_list()
    user_id_to_real_name = {
        user["id"]: user["real_name"]
        for user in users_response["members"]
        if not user.get("deleted", False)
    }

    channels = get_all_channels(client)

    for channel in channels:
        if channel.get("is_im", False):
            channel_id = channel["id"]
            user_id = channel["user"]
            real_name = user_id_to_real_name.get(user_id, "Unknown User")
            channel_to_name[channel_id] = real_name
        elif channel.get("is_mpim", False):
            channel_id = channel["id"]
            channel_name = channel["name"]
            channel_to_name[channel_id] = channel_name
        else:
            # public or private channel
            channel_id = channel["id"]
            channel_name = channel["name"]
            channel_to_name[channel_id] = channel_name

    return channel_to_name, user_id_to_real_name


def get_matches(query, choices):
    return process.extract(query, choices, limit=10)


def get_matches_for_name(query, favourite_names, all_names, name2channelid):
    matches_in_favourites = get_matches(query, favourite_names)
    matches_including_ids = [(*m, name2channelid[m[0]]) for m in matches_in_favourites]
    matches_in_favourites_list = [
        MatchedContact(query=query, name=m[0], score=m[1], channel_id=m[3])
        for m in matches_including_ids
    ]

    matches_in_all = get_matches(query, all_names)
    matches_including_ids = [(*m, name2channelid[m[0]]) for m in matches_in_all]
    matches_in_all_list = [
        MatchedContact(query=query, name=m[0], score=m[1], channel_id=m[3])
        for m in matches_including_ids
    ]

    return NamesMatchResponse(
        matches_in_favourites=matches_in_favourites_list,
        matches_in_all=matches_in_all_list,
    )
