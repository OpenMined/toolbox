import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rapidfuzz import process

from whatsapp_desktop_mcp.models import (
    ChatResponse,
    ContactMatch,
    ContactMatchResponse,
    MessageResponse,
)

SQLITE_DB_PATH = Path(
    "~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
).expanduser()
db = sqlite3.connect(str(SQLITE_DB_PATH))


# Function: Seconds since Jan 1, 2001 UTC (WhatsApp/iOS epoch)
def get_timestamp_since_2001(dt):
    epoch_2001 = datetime(2001, 1, 1, tzinfo=timezone.utc)
    return int((dt - epoch_2001).total_seconds())


# Function: Convert WhatsApp timestamp to datetime
def whatsapp_timestamp_to_datetime(timestamp):
    epoch_2001 = datetime(2001, 1, 1, tzinfo=timezone.utc)
    return epoch_2001 + timedelta(seconds=timestamp)


def get_all_chat_names():
    query = """
    SELECT
        ZWACHATSESSION.ZPARTNERNAME as chat_name,
        ZWACHATSESSION.ZCONTACTJID as chat_jid
    FROM
        ZWACHATSESSION
    WHERE
        ZWACHATSESSION.ZSESSIONTYPE < 2
    """
    cursor = db.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return results


def db_get_message_by_contact_id(contact_id: str, n_days_ago=7):
    now = datetime.now(timezone.utc)
    n_days_ago_date = (now - timedelta(days=n_days_ago)).date()
    n_days_ago_datetime = datetime.combine(
        n_days_ago_date, datetime.min.time(), tzinfo=timezone.utc
    )
    n_days_ago_timestamp = get_timestamp_since_2001(n_days_ago_datetime)

    query = """
    SELECT
        ZWACHATSESSION.ZCONTACTJID as chat_jid,
        ZWACHATSESSION.ZPARTNERNAME as chat_name,
        ZWAMESSAGE.ZTEXT as message_text,
        ZWAMESSAGE.ZMESSAGEDATE as message_date,
        ZWAPROFILEPUSHNAME.ZPUSHNAME as sender_name,
        ZWACHATSESSION.ZSESSIONTYPE = 1 as is_group_chat
    FROM
        ZWACHATSESSION
    JOIN
        ZWAMESSAGE ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
    JOIN
        ZWAPROFILEPUSHNAME ON ZWAPROFILEPUSHNAME.ZJID = ZWAMESSAGE.ZFROMJID
    WHERE
        ZWAMESSAGE.ZMESSAGEDATE >= ? AND
        ZWACHATSESSION.ZCONTACTJID = ?
        AND ZWAMESSAGE.ZTEXT IS NOT NULL
    ORDER BY
        ZWAMESSAGE.ZMESSAGEDATE DESC
    """
    cursor = db.cursor()
    cursor.execute(query, (n_days_ago_timestamp, contact_id))
    results = cursor.fetchall()
    return results


# Get the start of the current week (Monday)


def get_all_messages(n_days_ago=7):
    now = datetime.now(timezone.utc)
    n_days_ago_date = (now - timedelta(days=n_days_ago)).date()
    n_days_ago_datetime = datetime.combine(
        n_days_ago_date, datetime.min.time(), tzinfo=timezone.utc
    )
    n_days_ago_timestamp = get_timestamp_since_2001(n_days_ago_datetime)

    query = """
    SELECT
        ZWACHATSESSION.ZCONTACTJID as chat_jid,
        ZWACHATSESSION.ZPARTNERNAME as chat_name,
        ZWAMESSAGE.ZTEXT as message_text,
        ZWAMESSAGE.ZMESSAGEDATE as message_date,
        ZWAPROFILEPUSHNAME.ZPUSHNAME as sender_name,
        ZWACHATSESSION.ZSESSIONTYPE =1 as is_group_chat

    FROM
        ZWACHATSESSION
    JOIN
        ZWAMESSAGE ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
    JOIN ZWAPROFILEPUSHNAME ON ZWAPROFILEPUSHNAME.ZJID = ZWAMESSAGE.ZFROMJID
    WHERE
        ZWAMESSAGE.ZMESSAGEDATE >= ? -- WhatsApp stores dates as unix timestamps
        and ZWAMESSAGE.ZTEXT is not null
        and ZWACHATSESSION.ZSESSIONTYPE < 2
    ORDER BY
        chat_jid, message_date
    """

    cursor = db.cursor()
    cursor.execute(query, (n_days_ago_timestamp,))
    results = cursor.fetchall()
    return results


def get_matches(query, choices):
    return process.extract(query, choices, limit=10)


def get_chat_id_for_name(query_name: str):
    chat_name_id_tuples = get_all_chat_names()
    chat_names = [x[0] for x in chat_name_id_tuples]

    match_tuples = get_matches(query_name, chat_names)

    match_results = []
    for match in match_tuples:
        contact_name = match[0]
        contact_id = chat_name_id_tuples[match[2]][1]
        score = match[1]
        match_results.append(
            ContactMatch(
                query=query_name,
                contact_name=contact_name,
                contact_id=contact_id,
                score=score,
            )
        )
    return ContactMatchResponse(matches=match_results)


def get_message_by_contact_id(contact_id: str, n_days_ago=300):
    rows = db_get_message_by_contact_id(contact_id, n_days_ago=300)
    if len(rows) > 0:
        messages = [MessageResponse.from_sql_row(row) for row in rows]
        response = ChatResponse(chat_name=messages[0].chat_name, messages=messages)
    else:
        response = ChatResponse(chat_name=None, messages=[])
    return response


def get_recent_messages(n_days_ago=7):
    chat_messages = get_all_messages(n_days_ago=n_days_ago)

    from collections import defaultdict

    # Group messages by chat name
    chats_dict = defaultdict(list)
    for x in chat_messages:
        message = MessageResponse.from_sql_row(x)
        chats_dict[message.chat_name].append(message)

    chats = [
        ChatResponse(chat_name=chat_name, messages=messages)
        for chat_name, messages in chats_dict.items()
    ]

    return chats
