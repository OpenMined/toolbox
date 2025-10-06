import time
import urllib
from datetime import datetime

from omni.twitter import account_exists, get_guest_token

# warmup
cookie_value, expires = get_guest_token()
datetime_expires = datetime.fromtimestamp(expires)

cookie_decoded = urllib.parse.unquote(cookie_value)

time_start = time.time()
cookie_value, expires = get_guest_token()
handle = "elonmusk"
# handle = "XXXXXFQWEGWRBFSD"
exists = account_exists(handle, cookie_value)


time_end = time.time()
print(f"Time taken: {time_end - time_start} seconds")
if exists:
    print(f"Account {handle} exists")
else:
    print(f"Account {handle} does not exist")
