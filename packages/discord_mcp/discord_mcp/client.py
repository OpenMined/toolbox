"""Discord API client with rate limiting and retry logic."""

import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Generator
from urllib.parse import quote, urlencode

import httpx

from discord_mcp.exceptions import (
    AuthenticationException,
    DiscordException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
)

logger = logging.getLogger(__name__)


class TokenKind(Enum):
    """Discord token types."""

    USER = "user"
    BOT = "bot"


class RateLimitPreference(Enum):
    """Rate limiting preferences."""

    IGNORE_ALL = "ignore_all"
    RESPECT_FOR_USER_TOKENS = "respect_for_user_tokens"
    RESPECT_FOR_BOT_TOKENS = "respect_for_bot_tokens"
    RESPECT_ALL = "respect_all"


class DiscordClient:
    """Discord API client with rate limiting and retry logic."""

    BASE_URL = "https://discord.com/api/v10"
    MAX_RETRIES = 8
    INITIAL_DELAY = 1.0
    MAX_DELAY = 60.0

    def __init__(
        self,
        token: str,
        rate_limit_preference: RateLimitPreference = RateLimitPreference.RESPECT_ALL,
    ):
        """Initialize Discord client.

        Args:
            token: Discord token (user or bot)
            rate_limit_preference: How to handle rate limits
        """
        self.token = token
        self.rate_limit_preference = rate_limit_preference
        self._resolved_token_kind: Optional[TokenKind] = None
        self._session = httpx.Client(timeout=30.0)

    def close(self):
        """Close the HTTP session."""
        if self._session:
            self._session.close()

    def __enter__(self):
        """Context manager entry for backward compatibility."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for backward compatibility."""
        self.close()

    def _should_respect_rate_limits(self, token_kind: TokenKind) -> bool:
        """Check if rate limits should be respected for the given token kind."""
        if self.rate_limit_preference == RateLimitPreference.IGNORE_ALL:
            return False
        elif self.rate_limit_preference == RateLimitPreference.RESPECT_FOR_USER_TOKENS:
            return token_kind == TokenKind.USER
        elif self.rate_limit_preference == RateLimitPreference.RESPECT_FOR_BOT_TOKENS:
            return token_kind == TokenKind.BOT
        else:  # RESPECT_ALL
            return True

    def _get_auth_header(self, token_kind: TokenKind) -> str:
        """Get the authorization header value for the given token kind."""
        if token_kind == TokenKind.BOT:
            return f"Bot {self.token}"
        else:
            return self.token

    def _resolve_token_kind(self) -> TokenKind:
        """Resolve the token kind by attempting authentication."""
        if self._resolved_token_kind is not None:
            return self._resolved_token_kind

        # Try user token first
        try:
            self._make_request("GET", "users/@me", token_kind=TokenKind.USER)
            self._resolved_token_kind = TokenKind.USER
            return TokenKind.USER
        except AuthenticationException:
            pass

        # Try bot token
        try:
            self._make_request("GET", "users/@me", token_kind=TokenKind.BOT)
            self._resolved_token_kind = TokenKind.BOT
            return TokenKind.BOT
        except AuthenticationException:
            pass

        raise AuthenticationException("Authentication token is invalid")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        token_kind: Optional[TokenKind] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a request to the Discord API with retry logic and rate limiting."""
        if not self._session:
            raise RuntimeError("Client session is closed.")

        if token_kind is None:
            token_kind = self._resolve_token_kind()

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": self._get_auth_header(token_kind),
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://discord.com/channels/@me",
            "Origin": "https://discord.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self._session.request(method, url, headers=headers, **kwargs)

                # Handle rate limiting before checking response status
                if self._should_respect_rate_limits(token_kind):
                    self._handle_rate_limiting(response)

                # Check for HTTP errors
                if response.status_code == 401:
                    raise AuthenticationException("Authentication token is invalid")
                elif response.status_code == 403:
                    raise ForbiddenException(
                        f"Request to '{endpoint}' failed: forbidden"
                    )
                elif response.status_code == 404:
                    raise NotFoundException(
                        f"Request to '{endpoint}' failed: not found"
                    )
                elif response.status_code == 429:
                    # Handle rate limiting
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        delay = float(retry_after) + 1.0  # Add 1 second buffer
                        logger.warning(f"Rate limited. Waiting {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        # Fallback to exponential backoff
                        delay = min(
                            self.INITIAL_DELAY * (2**attempt) + 1, self.MAX_DELAY
                        )
                        time.sleep(delay)
                        continue
                elif response.status_code >= 400:
                    error_text = response.text
                    raise DiscordException(
                        f"Request to '{endpoint}' failed with status {response.status_code}: {error_text}"
                    )

                # Parse JSON response
                return response.json()

            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt == self.MAX_RETRIES:
                    raise DiscordException(
                        f"Request failed after {self.MAX_RETRIES} retries: {e}"
                    )

                # Exponential backoff
                delay = min(self.INITIAL_DELAY * (2**attempt) + 1, self.MAX_DELAY)
                logger.warning(
                    f"Request failed (attempt {attempt + 1}), retrying in {delay} seconds..."
                )
                time.sleep(delay)

        raise DiscordException("Maximum retries exceeded")

    def _handle_rate_limiting(self, response: httpx.Response) -> None:
        """Handle Discord's advisory rate limiting."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_after = response.headers.get("X-RateLimit-Reset-After")

        if remaining is not None and reset_after is not None:
            remaining_requests = int(remaining)
            reset_delay = float(reset_after)

            # If this was the last request before hitting rate limit, wait
            if remaining_requests <= 0:
                delay = min(reset_delay + 1.0, self.MAX_DELAY)  # Add 1 second buffer
                logger.info(
                    f"Proactive rate limit handling. Waiting {delay} seconds..."
                )
                time.sleep(delay)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        try:
            return self._make_request("GET", f"users/{user_id}")
        except NotFoundException:
            return None

    def get_current_user(self) -> Dict[str, Any]:
        """Get the current authenticated user."""
        return self._make_request("GET", "users/@me")

    def get_guild_channels(
        self, guild_id: str
    ) -> Generator[Dict[str, Any], None, None]:
        """Get all channels in a guild."""
        if guild_id == "@me":
            # Get DM channels
            response = self._make_request("GET", "users/@me/channels")
            for channel in response:
                yield channel
        else:
            response = self._make_request("GET", f"guilds/{guild_id}/channels")
            # Sort channels by position, then by ID
            channels = sorted(
                response, key=lambda c: (c.get("position", 0), int(c["id"]))
            )
            for channel in channels:
                yield channel

    def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information."""
        return self._make_request("GET", f"channels/{channel_id}")

    def get_messages(
        self,
        channel_id: str,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100,
    ) -> Generator[Dict[str, Any], None, None]:
        """Get messages from a channel."""
        current_after = after or "0"

        while True:
            params = {"limit": str(min(limit, 100))}
            if current_after != "0":
                params["after"] = current_after
            if before:
                params["before"] = before

            response = self._make_request(
                "GET", f"channels/{channel_id}/messages?{urlencode(params)}"
            )

            if not response:
                break

            # Messages are returned newest to oldest, so reverse them
            messages = list(reversed(response))

            for message in messages:
                yield message
                current_after = message["id"]

            if len(response) < min(limit, 100):
                break

    def get_messages_since(
        self,
        channel_id: str,
        since: datetime,
        until: Optional[datetime] = None,
        before: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Get messages from a channel since a specific datetime."""
        # Convert datetime to Discord snowflake (approximate)
        timestamp_ms = int(since.timestamp() * 1000)
        discord_epoch = 1420070400000  # Discord epoch: January 1, 2015
        snowflake = str((timestamp_ms - discord_epoch) << 22)

        # Convert until datetime to snowflake if provided
        until_snowflake = before
        if until and not before:
            until_ms = int(until.timestamp() * 1000)
            until_snowflake = str((until_ms - discord_epoch) << 22)

        for message in self.get_messages(
            channel_id, after=snowflake, before=until_snowflake
        ):
            # Parse message timestamp
            message_time = datetime.fromisoformat(
                message["timestamp"].replace("Z", "+00:00")
            )
            # Convert since to UTC if it's naive
            if since.tzinfo is None:
                since = since.replace(tzinfo=message_time.tzinfo)
            if until and until.tzinfo is None:
                until = until.replace(tzinfo=message_time.tzinfo)

            # Check if message is in the time range
            if message_time >= since:
                if until is None or message_time <= until:
                    yield message
                elif message_time > until:
                    # We've gone beyond the until time, stop
                    break

    def get_user_guilds(self) -> Generator[Dict[str, Any], None, None]:
        """Get all guilds for the authenticated user."""
        # Add Direct Messages as a special "guild"
        yield {
            "id": "@me",
            "name": "Direct Messages",
            "icon": None,
        }

        after = "0"
        while True:
            params = {"limit": "100", "after": after}
            response = self._make_request(
                "GET", f"users/@me/guilds?{urlencode(params)}"
            )

            if not response:
                break

            for guild in response:
                yield guild
                after = guild["id"]

            if len(response) < 100:
                break

    def get_guild(self, guild_id: str) -> Dict[str, Any]:
        """Get guild information."""
        if guild_id == "@me":
            return {
                "id": "@me",
                "name": "Direct Messages",
                "icon": None,
            }
        return self._make_request("GET", f"guilds/{guild_id}")

    def get_member_roles(self, guild_id: str, user_id: str) -> List[str]:
        """Get the roles for a guild member."""
        try:
            member_data = self._make_request(
                "GET", f"guilds/{guild_id}/members/{user_id}"
            )
            return member_data.get("roles", [])
        except Exception as e:
            logger.warning(f"Could not get member data for guild {guild_id}: {e}")
            return []

    def get_guild_roles(self, guild_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all roles in a guild."""
        try:
            roles_data = self._make_request("GET", f"guilds/{guild_id}/roles")
            return {role["id"]: role for role in roles_data}
        except Exception as e:
            logger.warning(f"Could not get roles for guild {guild_id}: {e}")
            return {}
