import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import keyring
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_browser_locations(browser: str) -> List[Path]:
    """Get the most likely cookie database locations for a browser."""
    home = Path.home()

    if browser.lower() == "chrome":
        base_path = home / "Library/Application Support/Google/Chrome"
        profiles = ["Default", "Profile 1", "Profile 2", "Profile 3"]
    elif browser.lower() == "brave":
        base_path = home / "Library/Application Support/BraveSoftware/Brave-Browser"
        profiles = ["Default", "Profile 1", "Profile 2", "Profile 3"]
    else:
        return []

    # Return cookie database paths that actually exist
    cookie_paths = []
    for profile in profiles:
        cookie_db = base_path / profile / "Cookies"
        if cookie_db.exists():
            cookie_paths.append(cookie_db)

    return cookie_paths


def decrypt_cookie_value(encrypted_value: bytes, browser: str) -> Optional[str]:
    """Decrypt a cookie value using the browser's keychain key."""
    if not encrypted_value or not encrypted_value.startswith(b"v10"):
        return None

    # Get encryption key from keychain
    if browser.lower() == "chrome":
        keychain_key = keyring.get_password("Chrome Safe Storage", "Chrome")
    elif browser.lower() == "brave":
        keychain_key = keyring.get_password("Brave Safe Storage", "Brave")
    else:
        return None

    if not keychain_key:
        return None

    # Derive encryption key using PBKDF2
    salt = b"saltysalt"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=16,
        salt=salt,
        iterations=1003,
    )
    key = kdf.derive(keychain_key.encode())

    # Decrypt the cookie
    try:
        ciphertext = encrypted_value[3:]  # Remove 'v10' prefix
        iv = b" " * 16  # Chromium uses 16 spaces as IV

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 padding
        padding_length = decrypted[-1]
        if isinstance(padding_length, int) and 1 <= padding_length <= 16:
            decrypted = decrypted[:-padding_length]

        # Convert to string
        return decrypted.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Decryption error: {e}")
        return None


def extract_xoxd_token_from_decrypted(decrypted_value: str) -> Optional[str]:
    """Extract and properly encode the xoxd token from decrypted cookie value."""
    if not decrypted_value:
        return None

    # Find xoxd token
    xoxd_start = decrypted_value.find("xoxd-")
    if xoxd_start == -1:
        return None

    # Extract from xoxd onwards
    remaining = decrypted_value[xoxd_start:]

    # Check if already URL encoded
    if "%" in remaining[:50]:
        # Already encoded, extract until non-token character
        token = remaining.split("\x00")[0].split(" ")[0]
        return token
    else:
        # Not encoded, extract and encode
        token_end = 5  # Start after 'xoxd-'
        valid_chars = (
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=-_"
        )

        while token_end < len(remaining) and remaining[token_end] in valid_chars:
            token_end += 1

        raw_token = remaining[:token_end]

        # URL encode everything after 'xoxd-'
        prefix = "xoxd-"
        token_body = raw_token[5:]
        encoded_body = quote(token_body, safe="")

        return prefix + encoded_body


def try_get_cookie_from_browser(browser: str) -> Optional[str]:
    """Try to get the Slack xoxd cookie from a specific browser."""
    print(f"\nTrying to extract cookie from {browser}...")

    # Get possible cookie locations
    cookie_paths = get_browser_locations(browser)
    if not cookie_paths:
        print(f"No {browser} profiles found")
        return None

    print(f"Found {len(cookie_paths)} {browser} profile(s)")

    # Try each profile
    for cookie_path in cookie_paths:
        profile_name = cookie_path.parent.name
        print(f"Checking {browser} {profile_name}...")

        # Copy database (browser locks it)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            temp_path = tmp.name

        try:
            shutil.copy2(cookie_path, temp_path)

            # Query for Slack 'd' cookie
            conn = sqlite3.connect(temp_path)
            conn.text_factory = bytes
            cursor = conn.cursor()

            cursor.execute("""
                SELECT encrypted_value
                FROM cookies
                WHERE host_key LIKE '%slack.com%' AND name = 'd'
                ORDER BY last_access_utc DESC
                LIMIT 1
            """)

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                # Decrypt the cookie
                decrypted = decrypt_cookie_value(result[0], browser)
                if decrypted:
                    # Extract the token
                    token = extract_xoxd_token_from_decrypted(decrypted)
                    if token:
                        print(
                            f"Successfully extracted token from {browser} {profile_name}"
                        )
                        os.unlink(temp_path)
                        return token

            os.unlink(temp_path)

        except Exception as e:
            print(f"Error reading {profile_name}: {e}")
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    return None


def get_slack_xoxd_cookie_from_browser_cookie_files() -> str:
    """
    Get Slack xoxd cookie from Chrome or Brave.

    Returns:
        str: The xoxd cookie token

    Raises:
        ValueError: If no cookie could be found in either browser
    """
    # Try Chrome first
    token = try_get_cookie_from_browser("chrome")
    if token:
        return token

    # Try Brave if Chrome failed
    token = try_get_cookie_from_browser("brave")
    if token:
        return token

    # Both failed
    raise ValueError(
        "Could not find Slack xoxd cookie in Chrome or Brave. "
        "Make sure you are logged into Slack in one of these browsers."
    )


# Usage example
if __name__ == "__main__":
    try:
        xoxd_cookie = get_slack_xoxd_cookie_from_browser_cookie_files()
        import os

        from slack_sdk import WebClient

        slack_token = os.getenv("SLACK_TOKEN")  # Your API token (xoxc-...)
        d_cookie = "{xoxd_cookie}"

        headers = {{"Cookie": "d={d_cookie}", "User-Agent": "Mozilla/5.0"}}
        client = WebClient(token=slack_token, headers=headers)

        response = client.auth_test()
        print(response.data)

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged into Slack in Chrome or Brave")
        print("2. Try logging out and back in to refresh the cookie")
        print("3. Check that the browser has saved the cookie (not in incognito mode)")
