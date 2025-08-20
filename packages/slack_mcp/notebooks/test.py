# part 1
import sqlite3
from pathlib import Path

cookie_file = Path("/Users/koen/Library/Application Support/Slack/Cookies").expanduser()
conn = sqlite3.connect(f"file:{cookie_file}")
sql = "select 1;"

with conn:
    row = conn.execute(sql).fetchone()

    from time import sleep

    sleep(2)
    from toolbox.store.callbacks.auth.auth_slack_keyring import get_tokens

    print(get_tokens())
