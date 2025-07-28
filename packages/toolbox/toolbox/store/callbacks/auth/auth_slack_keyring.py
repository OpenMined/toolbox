import json
import os
import pathlib
import shutil
import sys
import tempfile

# import leveldb
import pycookiecheat
from pathlib import Path


def get_slack_leveldb_path():
    if sys.platform == "darwin":
        option1 = Path(
            "~/Library/Application Support/Slack/Local Storage/leveldb"
        ).expanduser()
        option2 = Path(
            "~/Library/Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack/Local Storage/leveldb"
        ).expanduser()
        if option1.exists():
            return option1
        elif option2.exists():
            return option2
        else:
            raise ValueError("Slack's Local Storage not found. Aborting.")
    elif sys.platform.startswith("linux"):
        return Path("~/.config/Slack/Local Storage/leveldb").expanduser()
    else:
        raise ValueError("windows not supported.")


SLACK_LEVELDB_PATH = get_slack_leveldb_path()


def get_cookie():
    cookies = pycookiecheat.chrome_cookies("http://slack.com", browser="Slack")
    return cookies["d"]


def get_tokens_and_cookie():
    return {"tokens": get_tokens(), "cookie": get_cookie()}


def try_to_copy_and_read_leveldb(leveldb_path):
    tmpdir = Path(tempfile.mkdtemp())
    tmp_leveldb_path = tmpdir / "leveldb"
    shutil.copytree(str(leveldb_path), str(tmp_leveldb_path))
    lock_file = tmp_leveldb_path / "LOCK"
    if lock_file.exists():
        lock_file.unlink()
    return None
    # db = leveldb.LevelDB(str(tmp_leveldb_path))
    # return db


def get_config(db):
    try:
        cfg = next(v for k, v in db.RangeIter() if bytearray(b"localConfig_v2") in k)
    except StopIteration as e:
        raise RuntimeError(
            "Slack's Local Storage not recognised: localConfig not found. Aborting."
        ) from e

    try:
        import re

        def remove_control_chars(s):
            # Remove all non-printable control characters (ASCII 0–31), except \n, \r, \t
            return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", s)

        decoded_cfg = cfg[1:].decode("utf-8")
        cleaned_cfg = remove_control_chars(decoded_cfg)
        try:
            return json.loads(cleaned_cfg)
        except Exception:
            # attempt to fix the json, no idea why this is sometimes missing
            cleaned_cfg = cleaned_cfg + "}"
            return json.loads(cleaned_cfg)
    except Exception as e:
        raise RuntimeError(
            "Slack's Local Storage not recognised: localConfig not in expected format. Aborting."
        ) from e


def get_tokens():
    db = None
    try:
        db = leveldb.LevelDB(str(SLACK_LEVELDB_PATH))
        config = get_config(db)

    except Exception as e:
        try:
            db = try_to_copy_and_read_leveldb(SLACK_LEVELDB_PATH)
            config = get_config(db)
        except Exception:
            if db:
                del db
            raise RuntimeError(
                "Could not read Slack's Local Storage database. Have you quit Slack?"
            ) from e
    finally:
        if db:
            del db

    tokens = {}
    for v in config["teams"].values():
        if not isinstance(v, dict) or "name" not in v or "token" not in v:
            continue
        tokens[v["url"]] = {"token": v["token"], "name": v["name"]}

    return tokens


if __name__ == "__main__":
    print(get_tokens_and_cookie())
