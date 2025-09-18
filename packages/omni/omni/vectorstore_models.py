import json
import sqlite3
from typing import Any

from toolbox_store import TBDocument


class Tweet(TBDocument):
    """Tweet document model for ToolboxStore"""

    # Core tweet fields
    tweet_id: str
    author: dict[str, Any]  # JSON structure for author data
    created_at_tweet: str  # Tweet's created_at timestamp
    conversation_id: str | None = None
    in_reply_to_user_id: str | None = None
    in_reply_to_status_id: str | None = None
    lang: str | None = None

    # Engagement metrics
    retweet_count: int = 0
    favorite_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    bookmark_count: int = 0
    view_count: int = 0

    # Status flags
    is_quote_status: bool = False
    possibly_sensitive: bool = False
    retweeted: bool = False
    favorited: bool = False
    bookmarked: bool = False

    # Additional content
    note_tweet_text: str | None = None
    media_urls: str | None = None
    urls: str | None = None
    hashtags: str | None = None
    user_mentions: str | None = None
    source_platform: str | None = None

    # Tweet type classification and context (Hybrid approach)
    tweet_type: str = "original"  # "original", "repost", "quote", "reply"
    interaction_context: dict[str, Any] = {
        "is_repost": False,
        "original_tweet_id": None,
        "original_author": None,
        "quoted_tweet": None,  # Full quoted tweet object
        "reply_to": None,  # Reply context
        "repost_comment": None,  # Comment added during repost
    }

    @classmethod
    def schema_extra_columns(cls) -> list[tuple[str, str]]:
        return [
            ("tweet_id", "TEXT UNIQUE"),
            ("author", "TEXT"),  # JSON
            ("created_at_tweet", "TEXT"),
            ("conversation_id", "TEXT"),
            ("in_reply_to_user_id", "TEXT"),
            ("in_reply_to_status_id", "TEXT"),
            ("lang", "TEXT"),
            ("retweet_count", "INTEGER"),
            ("favorite_count", "INTEGER"),
            ("reply_count", "INTEGER"),
            ("quote_count", "INTEGER"),
            ("bookmark_count", "INTEGER"),
            ("view_count", "INTEGER"),
            ("is_quote_status", "BOOLEAN"),
            ("possibly_sensitive", "BOOLEAN"),
            ("retweeted", "BOOLEAN"),
            ("favorited", "BOOLEAN"),
            ("bookmarked", "BOOLEAN"),
            ("note_tweet_text", "TEXT"),
            ("media_urls", "TEXT"),
            ("urls", "TEXT"),
            ("hashtags", "TEXT"),
            ("user_mentions", "TEXT"),
            ("source_platform", "TEXT"),
            ("tweet_type", "TEXT"),
            ("interaction_context", "TEXT"),  # JSON
        ]

    @classmethod
    def schema_extra(
        cls,
        documents_table: str,
        chunks_table: str,
        embeddings_table: str,
        fts_table: str,
    ) -> list[str]:
        return [
            f"CREATE INDEX IF NOT EXISTS idx_{documents_table}_tweet_id ON {documents_table} (tweet_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{documents_table}_created_at_tweet ON {documents_table} (created_at_tweet)",
            f"CREATE INDEX IF NOT EXISTS idx_{documents_table}_conversation_id ON {documents_table} (conversation_id)",
        ]

    @classmethod
    def from_instruction_entry(cls, tweet_result: dict[str, Any]) -> "Tweet | None":
        """Parse a single tweet from a tweet_results JSON structure"""
        result = tweet_result.get("result", {})
        tweet_id = result.get("rest_id")
        if not tweet_id:
            return None

        # Extract author - try multiple possible locations
        author_data = {"screen_name": "Unknown", "name": "Unknown", "avatar_url": ""}

        # Try core.user_results first
        if "core" in result and "user_results" in result["core"]:
            user_result = result["core"]["user_results"].get("result", {})

            # Get avatar from avatar.image_url
            if "avatar" in user_result:
                author_data["avatar_url"] = user_result["avatar"].get("image_url", "")

            if "core" in user_result:
                author_data["screen_name"] = user_result["core"].get(
                    "screen_name", "Unknown"
                )
                author_data["name"] = user_result["core"].get("name", "Unknown")

            # Also check legacy within user_result
            if "legacy" in user_result:
                user_legacy = user_result["legacy"]
                author_data["screen_name"] = user_legacy.get(
                    "screen_name", author_data["screen_name"]
                )
                author_data["name"] = user_legacy.get("name", author_data["name"])
                # Use legacy profile_image_url_https as fallback
                if not author_data["avatar_url"]:
                    author_data["avatar_url"] = user_legacy.get(
                        "profile_image_url_https", ""
                    )

        # Fallback: check if there's author info in the main legacy section
        legacy = result.get("legacy", {})
        if legacy and "user" in legacy:
            user_data = legacy["user"]
            author_data["screen_name"] = user_data.get(
                "screen_name", author_data["screen_name"]
            )
            author_data["name"] = user_data.get("name", author_data["name"])
            author_data["avatar_url"] = user_data.get(
                "profile_image_url_https", author_data["avatar_url"]
            )

        # Extract content and basic tweet info
        legacy = result.get("legacy", {})
        if not legacy:
            return None

        content = legacy.get("full_text", "")
        if "note_tweet" in result:
            note_results = result["note_tweet"].get("note_tweet_results", {})
            if "result" in note_results:
                content = note_results["result"].get("text", "")

        if not content:
            return None

        # Extract conversation and reply fields
        conversation_id = legacy.get("conversation_id_str")
        in_reply_to_status_id = legacy.get("in_reply_to_status_id_str")
        in_reply_to_user_id = legacy.get("in_reply_to_user_id_str")

        # Determine tweet type and extract interaction context
        tweet_type = "original"
        interaction_context = {
            "is_repost": False,
            "original_tweet_id": None,
            "original_author": None,
            "quoted_tweet": None,
            "reply_to": None,
            "repost_comment": None,
        }

        # Check for retweet
        if legacy.get("retweeted_status_result"):
            tweet_type = "repost"
            interaction_context["is_repost"] = True

            # Extract original tweet data
            rt_result = legacy["retweeted_status_result"]["result"]
            rt_legacy = rt_result.get("legacy", {})

            # Get original author
            original_author = {
                "screen_name": "Unknown",
                "name": "Unknown",
                "avatar_url": "",
            }
            if "core" in rt_result and "user_results" in rt_result["core"]:
                rt_user_result = rt_result["core"]["user_results"].get("result", {})
                if "avatar" in rt_user_result:
                    original_author["avatar_url"] = rt_user_result["avatar"].get(
                        "image_url", ""
                    )
                if "core" in rt_user_result:
                    original_author["screen_name"] = rt_user_result["core"].get(
                        "screen_name", "Unknown"
                    )
                    original_author["name"] = rt_user_result["core"].get(
                        "name", "Unknown"
                    )
                if "legacy" in rt_user_result:
                    rt_user_legacy = rt_user_result["legacy"]
                    original_author["screen_name"] = rt_user_legacy.get(
                        "screen_name", original_author["screen_name"]
                    )
                    original_author["name"] = rt_user_legacy.get(
                        "name", original_author["name"]
                    )
                    if not original_author["avatar_url"]:
                        original_author["avatar_url"] = rt_user_legacy.get(
                            "profile_image_url_https", ""
                        )

            interaction_context["original_tweet_id"] = rt_result.get("rest_id")
            interaction_context["original_author"] = original_author
            interaction_context["repost_comment"] = content  # The RT @user: ... text

            # For reposts, use the original content as the main content
            content = rt_legacy.get("full_text", "")

        # Check for quote tweet
        elif legacy.get("is_quote_status") and result.get("quoted_status_result"):
            tweet_type = "quote"

            # Extract quoted tweet data
            qt_result = result["quoted_status_result"]["result"]
            qt_legacy = qt_result.get("legacy", {})

            # Get quoted author
            quoted_author = {
                "screen_name": "Unknown",
                "name": "Unknown",
                "avatar_url": "",
            }
            if "core" in qt_result and "user_results" in qt_result["core"]:
                qt_user_result = qt_result["core"]["user_results"].get("result", {})
                if "avatar" in qt_user_result:
                    quoted_author["avatar_url"] = qt_user_result["avatar"].get(
                        "image_url", ""
                    )
                if "core" in qt_user_result:
                    quoted_author["screen_name"] = qt_user_result["core"].get(
                        "screen_name", "Unknown"
                    )
                    quoted_author["name"] = qt_user_result["core"].get(
                        "name", "Unknown"
                    )
                if "legacy" in qt_user_result:
                    qt_user_legacy = qt_user_result["legacy"]
                    quoted_author["screen_name"] = qt_user_legacy.get(
                        "screen_name", quoted_author["screen_name"]
                    )
                    quoted_author["name"] = qt_user_legacy.get(
                        "name", quoted_author["name"]
                    )
                    if not quoted_author["avatar_url"]:
                        quoted_author["avatar_url"] = qt_user_legacy.get(
                            "profile_image_url_https", ""
                        )

            interaction_context["quoted_tweet"] = {
                "id": qt_result.get("rest_id"),
                "content": qt_legacy.get("full_text", ""),
                "author": quoted_author,
                "created_at": qt_legacy.get("created_at", ""),
                "favorite_count": qt_legacy.get("favorite_count", 0),
                "retweet_count": qt_legacy.get("retweet_count", 0),
            }

        # Check for reply
        elif in_reply_to_status_id:
            tweet_type = "reply"
            interaction_context["reply_to"] = {
                "status_id": in_reply_to_status_id,
                "user_id": in_reply_to_user_id,
            }

        return cls(
            id=tweet_id,
            tweet_id=tweet_id,
            content=content,
            author=author_data,
            source="twitter",
            created_at_tweet=legacy.get("created_at", ""),
            conversation_id=conversation_id,
            in_reply_to_user_id=in_reply_to_user_id,
            in_reply_to_status_id=in_reply_to_status_id,
            lang=legacy.get("lang"),
            retweet_count=legacy.get("retweet_count", 0),
            favorite_count=legacy.get("favorite_count", 0),
            tweet_type=tweet_type,
            interaction_context=interaction_context,
        )

    @classmethod
    def from_sql_row(cls, row: dict[str, Any] | sqlite3.Row) -> "Tweet":
        """Create a Tweet instance from a SQL row with proper JSON parsing."""
        if not isinstance(row, dict):
            row_dict = dict(row)
        else:
            row_dict = row.copy()

        # Parse JSON fields
        if "metadata" in row_dict and isinstance(row_dict["metadata"], str):
            row_dict["metadata"] = json.loads(row_dict["metadata"])

        if "author" in row_dict and isinstance(row_dict["author"], str):
            row_dict["author"] = json.loads(row_dict["author"])

        if "interaction_context" in row_dict and isinstance(
            row_dict["interaction_context"], str
        ):
            row_dict["interaction_context"] = json.loads(
                row_dict["interaction_context"]
            )

        return cls.model_validate(row_dict)
