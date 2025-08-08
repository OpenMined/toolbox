"""Discord permission calculation utilities."""

from typing import Dict, List, Any, Optional
from discord_mcp.client import DiscordClient


# Discord Permission Constants
PERMISSIONS = {
    "VIEW_CHANNEL": 1 << 10,  # 1024 - Can view the channel
    "READ_MESSAGE_HISTORY": 1 << 16,  # 65536 - Can read message history
    "SEND_MESSAGES": 1 << 11,  # 2048 - Can send messages
}




def _calculate_base_permissions(
    member_roles: List[str], guild_roles: Dict[str, Dict[str, Any]]
) -> int:
    """Calculate base permissions from guild roles."""
    # Start with @everyone role permissions
    everyone_role = None
    for role in guild_roles.values():
        if role["name"] == "@everyone":
            everyone_role = role
            break

    if not everyone_role:
        print("  ⚠️  Could not find @everyone role")
        return 0

    permissions = int(everyone_role.get("permissions", "0"))

    # Add permissions from other roles
    for role_id in member_roles:
        if role_id in guild_roles:
            role_perms = int(guild_roles[role_id].get("permissions", "0"))
            permissions |= role_perms

    return permissions


def _apply_channel_overwrites(
    base_permissions: int,
    channel_overwrites: List[Dict[str, Any]],
    user_id: str,
    member_roles: List[str],
    everyone_role_id: str,
) -> int:
    """Apply channel-specific permission overwrites following Discord's algorithm."""
    # Start with base permissions
    permissions = base_permissions

    # Step 1: Apply @everyone role overwrites
    for overwrite in channel_overwrites:
        if (
            overwrite["type"] == 0 and overwrite["id"] == everyone_role_id
        ):  # @everyone role
            allow = int(overwrite.get("allow", "0"))
            deny = int(overwrite.get("deny", "0"))
            permissions = (permissions & ~deny) | allow
            break

    # Step 2: Apply role-specific overwrites (not @everyone)
    for overwrite in channel_overwrites:
        if (
            overwrite["type"] == 0
            and overwrite["id"] != everyone_role_id
            and overwrite["id"] in member_roles
        ):
            allow = int(overwrite.get("allow", "0"))
            deny = int(overwrite.get("deny", "0"))
            permissions = (permissions & ~deny) | allow

    # Step 3: Apply user-specific overwrites (highest priority)
    for overwrite in channel_overwrites:
        if overwrite["type"] == 1 and overwrite["id"] == user_id:  # User overwrite
            allow = int(overwrite.get("allow", "0"))
            deny = int(overwrite.get("deny", "0"))
            permissions = (permissions & ~deny) | allow

    return permissions


def _has_channel_access(permissions: int) -> bool:
    """Check if user has basic read access to a channel."""
    return (permissions & PERMISSIONS["VIEW_CHANNEL"]) and (
        permissions & PERMISSIONS["READ_MESSAGE_HISTORY"]
    )


def compute_channel_permissions(
    guild_id: str, client: DiscordClient
) -> Dict[str, bool]:
    """Analyze all channels in a guild and determine access via permission calculation."""
    print(f"\n📋 Analyzing guild: {guild_id}")

    # Get current user
    try:
        user = client.get_current_user()
        user_id = user["id"]
        print(f"  👤 User: {user['username']} ({user_id})")
    except Exception as e:
        print(f"  ❌ Could not get current user: {e}")
        return {}

    # Get member roles in this guild
    member_roles = client.get_member_roles(guild_id, user_id)
    print(f"  🎭 Member has {len(member_roles)} roles")

    # Get guild roles
    guild_roles = client.get_guild_roles(guild_id)
    print(f"  📝 Guild has {len(guild_roles)} total roles")

    # Find @everyone role ID (it's the same as guild ID)
    everyone_role_id = guild_id

    # Calculate base permissions
    base_permissions = _calculate_base_permissions(member_roles, guild_roles)
    print(f"  🔐 Base permissions: {base_permissions}")

    # Get all channels
    channels = list(client.get_guild_channels(guild_id))
    print(f"  📺 Found {len(channels)} channels")

    results = {}

    for channel in channels:
        channel_id = channel["id"]
        channel_name = channel.get("name", f"Channel-{channel_id}")
        channel_type = channel.get("type", 0)

        # Skip non-text channels
        if channel_type not in [0, 1, 5, 10, 11, 12]:  # Text channel types
            continue

        # Apply channel overwrites
        overwrites = channel.get("permission_overwrites", [])
        effective_permissions = _apply_channel_overwrites(
            base_permissions, overwrites, user_id, member_roles, everyone_role_id
        )

        # Check if user has access
        has_access = _has_channel_access(effective_permissions)

        results[channel_id] = has_access
        status = "✅ ACCESS" if has_access else "❌ NO ACCESS"
        print(f"    {status}: #{channel_name} ({channel_id})")

        # Debug: show permission details for failed channels
        if not has_access:
            can_view = bool(effective_permissions & PERMISSIONS["VIEW_CHANNEL"])
            can_read_history = bool(
                effective_permissions & PERMISSIONS["READ_MESSAGE_HISTORY"]
            )
            print(f"      View: {can_view}, Read History: {can_read_history}")

            # Show overwrites that might be blocking
            for overwrite in overwrites:
                if overwrite["type"] == 0 and overwrite["id"] in member_roles + [
                    everyone_role_id
                ]:
                    role_name = guild_roles.get(overwrite["id"], {}).get(
                        "name", overwrite["id"]
                    )
                    if overwrite["id"] == everyone_role_id:
                        role_name = "@everyone"
                    deny = int(overwrite.get("deny", "0"))
                    if deny & (
                        PERMISSIONS["VIEW_CHANNEL"]
                        | PERMISSIONS["READ_MESSAGE_HISTORY"]
                    ):
                        print(f"      🚫 Role {role_name} denies channel access")
                elif overwrite["type"] == 1 and overwrite["id"] == user_id:
                    deny = int(overwrite.get("deny", "0"))
                    if deny & (
                        PERMISSIONS["VIEW_CHANNEL"]
                        | PERMISSIONS["READ_MESSAGE_HISTORY"]
                    ):
                        print(f"      🚫 User-specific deny overwrite")

    return results
