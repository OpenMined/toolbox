"""Unit tests for Discord background worker functionality."""

import json
import random
import sqlite3
import string
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from discord_mcp.background_worker import (
    datetime_to_discord_timestamp,
    get_time_windows_to_fetch,
    parse_discord_timestamp,
    run_discord_mesage_download_and_write_background_worker_single,
)
from discord_mcp.client import DiscordClient
from discord_mcp.db import (
    get_discord_connection,
    get_earliest_timestamp_from_db,
    get_latest_timestamp_from_db,
    get_message_count,
)

from tests.mock_client import MockDiscordClient


def get_random_tmp_file():
    """Generate a random temporary filename under /tmp."""
    rand_str = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    return Path(f"/tmp/tmp_{rand_str}")


class TestableDiscordClient(MockDiscordClient):
    """Extended mock client that can return different data sets for time-based queries."""

    def __init__(self, token: str = "mock_token", **kwargs):
        super().__init__(token, **kwargs)
        self.current_data_set = "first_batch"  # Can be 'first_batch' or 'second_batch'

    def set_data_set(self, data_set: str):
        """Switch between different data sets for testing."""
        self.current_data_set = data_set

    def _adjust_message_timestamps(
        self, messages: List[Dict[str, Any]], days_old_start: int, days_old_end: int
    ) -> List[Dict[str, Any]]:
        """Adjust message timestamps to be between days_old_start and days_old_end days ago."""
        from datetime import timezone

        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days_old_start)
        end_time = now - timedelta(days=days_old_end)

        adjusted_messages = []
        for i, message in enumerate(messages):
            # Distribute messages evenly across the time window
            time_fraction = i / max(len(messages) - 1, 1)
            message_time = start_time + (end_time - start_time) * time_fraction
            adjusted_message = message.copy()
            adjusted_message["timestamp"] = message_time.isoformat()
            adjusted_messages.append(adjusted_message)

        return adjusted_messages

    def get_messages_since(
        self, channel_id: str, since: datetime, until=None, before=None
    ):
        """Override to return time-appropriate test data."""
        # Get base messages data
        messages_data = self._load_test_data("messages_with_users_test_data.json")
        if self.current_data_set == "first_batch":
            # Use only a small subset of messages for testing (first 10 messages)
            test_messages = messages_data["messages"][:10]
            days_old_start, days_old_end = 7, 4
        else:  # second_batch
            days_old_start, days_old_end = 4, 1
            test_messages = messages_data["messages"][10:20]

        # Adjust timestamps to be the right age
        messages = self._adjust_message_timestamps(
            test_messages, days_old_start, days_old_end
        )

        # Filter messages based on time window (since and until)
        filtered_messages = []
        for message in messages:
            message_time = datetime.fromisoformat(message["timestamp"])

            if message_time >= since:
                if until is None or message_time <= until:
                    filtered_messages.append(message)

        return filtered_messages


class TestBackgroundWorker:
    """Test Discord background worker functionality."""

    def setup_method(self):
        """Setup test database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        # Mock the database path
        self.db_path_patcher = patch(
            "discord_mcp.db.DISCORD_MCP_DB_PATH", Path(self.temp_db.name)
        )
        self.db_path_patcher.start()

    def teardown_method(self):
        """Cleanup after each test."""
        self.db_path_patcher.stop()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_time_window_logic_empty_db(self):
        """Test time window calculation when database is empty."""
        windows = get_time_windows_to_fetch(None, None, days_back=7)

        assert len(windows) == 1
        start_time, end_time = windows[0]

        # Should cover the last 7 days
        from datetime import timezone

        now = datetime.now(timezone.utc)
        expected_start = now - timedelta(days=7)

        # Allow some tolerance for test execution time
        assert abs((end_time - now).total_seconds()) < 60  # Within 1 minute of now
        assert (
            abs((start_time - expected_start).total_seconds()) < 60
        )  # Within 1 minute of expected

    def test_time_window_logic_with_data(self):
        """Test time window calculation when database has existing data."""
        from datetime import timezone

        now = datetime.now(timezone.utc)

        # Simulate existing data from 5 days ago to 2 days ago
        earliest_ts = datetime_to_discord_timestamp(now - timedelta(days=5))
        latest_ts = datetime_to_discord_timestamp(now - timedelta(days=2))

        windows = get_time_windows_to_fetch(earliest_ts, latest_ts, days_back=7)

        assert len(windows) == 2

        # First window should be from latest_ts to now (newer messages)
        newer_start, newer_end = windows[0]
        assert abs((newer_end - now).total_seconds()) < 60
        assert abs((newer_start - (now - timedelta(days=2))).total_seconds()) < 60

        # Second window should be from 7 days ago to earliest_ts (older messages)
        older_start, older_end = windows[1]
        assert abs((older_start - (now - timedelta(days=7))).total_seconds()) < 60
        assert abs((older_end - (now - timedelta(days=5))).total_seconds()) < 60

    def test_background_worker_single_run_two_batches(self):
        """Test that background worker correctly handles two time-separated batches of messages."""

        # Create testable client
        client = TestableDiscordClient("test_token")
        tmp_db_path = get_random_tmp_file()

        with get_discord_connection(tmp_db_path) as conn:
            # First run - should fetch messages from 7 days ago
            print("\n=== First run (7-4 days old messages) ===")
            client.set_data_set("first_batch")
            run_discord_mesage_download_and_write_background_worker_single(
                conn, client, guild_names=["Claude Developers"]
            )

            # Verify first batch data
            first_batch_count = get_message_count(conn)
            first_earliest = get_earliest_timestamp_from_db(conn)
            first_latest = get_latest_timestamp_from_db(conn)

            print(f"After first run: {first_batch_count} messages")
            print(f"Time range: {first_earliest} to {first_latest}")

            assert first_batch_count > 0, "First batch should contain messages"
            assert first_earliest is not None
            assert first_latest is not None

            # Verify the timestamps are roughly 7-4 days old
            earliest_dt = parse_discord_timestamp(first_earliest)
            latest_dt = parse_discord_timestamp(first_latest)
            from datetime import timezone

            now = datetime.now(timezone.utc)

            earliest_days_old = (now - earliest_dt).days
            latest_days_old = (now - latest_dt).days

            assert 3 <= latest_days_old <= 5, (
                f"Latest message should be ~4 days old, got {latest_days_old}"
            )
            assert 6 <= earliest_days_old <= 8, (
                f"Earliest message should be ~7 days old, got {earliest_days_old}"
            )

            # Second run - should fetch messages from 4-1 days ago
            print("\n=== Second run (4-1 days old messages) ===")
            client.set_data_set("second_batch")
            run_discord_mesage_download_and_write_background_worker_single(
                conn, client, guild_names=["Claude Developers"]
            )

            # Verify second batch data
            second_batch_count = get_message_count(conn)
            second_earliest = get_earliest_timestamp_from_db(conn)
            second_latest = get_latest_timestamp_from_db(conn)

            print(f"After second run: {second_batch_count} messages")
            print(f"Time range: {second_earliest} to {second_latest}")

            # Second run uses same message IDs so count stays the same (upsert replaces)
            # But we verify the time range has expanded to cover both batches
            second_earliest_dt = parse_discord_timestamp(second_earliest)
            second_latest_dt = parse_discord_timestamp(second_latest)

            # Time range should have expanded - latest should be newer (closer to now)
            assert second_latest_dt > latest_dt, (
                "Latest timestamp should move forward (newer messages)"
            )

            # Verify the new latest timestamp is roughly 1 day old (from second batch)
            if second_latest_dt.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=second_latest_dt.tzinfo)
            latest_days_old = (now - second_latest_dt).days
            assert 0 <= latest_days_old <= 2, (
                f"New latest message should be ~1 day old, got {latest_days_old}"
            )

            print(
                f"✅ Time range expanded from {(now - latest_dt).days} to {latest_days_old} days old"
            )

    def test_all_data_stored_correctly(self):
        """Test that messages, users, channels, and guilds are all stored correctly."""
        client = TestableDiscordClient("test_token")
        test_db_path = get_random_tmp_file().with_suffix(".sqlite")

        print(f"Test database path: {test_db_path}")

        with get_discord_connection(test_db_path) as conn:
            client.set_data_set("first_batch")
            run_discord_mesage_download_and_write_background_worker_single(
                conn, client, guild_names=["Claude Developers"]
            )

            # Check messages
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            assert message_count > 0, "Should have stored messages"

            # Check users
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            assert user_count > 0, "Should have stored users"

            # Check channels
            cursor.execute("SELECT COUNT(*) FROM channels")
            channel_count = cursor.fetchone()[0]
            assert channel_count > 0, "Should have stored channels"

            # Check guilds
            cursor.execute("SELECT COUNT(*) FROM guilds")
            guild_count = cursor.fetchone()[0]
            assert guild_count > 0, "Should have stored guilds"

            print(
                f"Stored: {message_count} messages, {user_count} users, {channel_count} channels, {guild_count} guilds"
            )

            # Verify data integrity - every message should have a valid author
            cursor.execute("""
                SELECT COUNT(*) FROM messages m 
                LEFT JOIN users u ON m.author_id = u.id 
                WHERE u.id IS NULL
            """)
            orphaned_messages = cursor.fetchone()[0]
            assert orphaned_messages == 0, "All messages should have valid users"

            # Verify every message has a valid channel
            cursor.execute("""
                SELECT COUNT(*) FROM messages m 
                LEFT JOIN channels c ON m.channel_id = c.id 
                WHERE c.id IS NULL
            """)
            orphaned_messages = cursor.fetchone()[0]
            assert orphaned_messages == 0, "All messages should have valid channels"

    def test_parse_discord_timestamp(self):
        """Test Discord timestamp parsing."""
        # Test with Z suffix
        dt1 = parse_discord_timestamp("2025-08-06T09:23:32.955000Z")
        assert dt1.year == 2025
        assert dt1.month == 8
        assert dt1.day == 6

        # Test with +00:00 suffix
        dt2 = parse_discord_timestamp("2025-08-06T09:23:32.955000+00:00")
        assert dt2.year == 2025
        assert dt2.month == 8
        assert dt2.day == 6

    def test_datetime_to_discord_timestamp(self):
        """Test converting datetime to Discord timestamp format."""
        dt = datetime(2025, 8, 6, 9, 23, 32, 955000)
        ts = datetime_to_discord_timestamp(dt)
        assert ts == "2025-08-06T09:23:32.955000Z"


class TestMockClientExtensions:
    """Test the extended mock client functionality."""

    def test_testable_client_data_switching(self):
        """Test that testable client can switch between data sets."""
        client = TestableDiscordClient("test_token")

        # Test first batch
        client.set_data_set("first_batch")
        from datetime import timezone

        messages_1 = list(
            client.get_messages_since(
                "test_channel", datetime.now(timezone.utc) - timedelta(days=10)
            )
        )

        # Test second batch
        client.set_data_set("second_batch")
        messages_2 = list(
            client.get_messages_since(
                "test_channel", datetime.now(timezone.utc) - timedelta(days=10)
            )
        )

        assert len(messages_1) > 0, "First batch should have messages"
        assert len(messages_2) > 0, "Second batch should have messages"

        # Messages should have different timestamps
        if messages_1 and messages_2:
            ts1 = parse_discord_timestamp(messages_1[0]["timestamp"])
            ts2 = parse_discord_timestamp(messages_2[0]["timestamp"])
            assert ts1 != ts2, "Different batches should have different timestamps"

    def test_message_timestamp_adjustment(self):
        """Test that message timestamps are correctly adjusted to be the right age."""
        client = TestableDiscordClient("test_token")
        client.set_data_set("first_batch")

        from datetime import timezone

        now = datetime.now(timezone.utc)
        since = now - timedelta(days=10)

        messages = list(client.get_messages_since("test_channel", since))

        assert len(messages) > 0, "Should have messages"

        for message in messages:
            msg_time = parse_discord_timestamp(message["timestamp"])
            days_old = (now - msg_time).days

            # Should be between 4-7 days old for first batch
            assert 3 <= days_old <= 8, (
                f"Message should be 4-7 days old, got {days_old} days"
            )
