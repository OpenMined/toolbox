"""Test utilities for Discord MCP tests."""

import random
import string
from pathlib import Path


def get_random_tmp_file():
    """Generate a random temporary filename under /tmp."""
    rand_str = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    return Path(f"/tmp/tmp_{rand_str}")
