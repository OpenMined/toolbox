from pathlib import Path

import toolbox_events
import watchfiles


async def watch_vault(vault_path: Path):
    """Watch the Obsidian vault for file changes and emit events."""
    async for changes in watchfiles.awatch(vault_path, debounce=5000, step=1000):
        for change_type, file_path in changes:
            # Skip hidden files and folder changes
            path = Path(file_path)
            if any(part.startswith(".") for part in path.parts) or path.is_dir():
                continue

            if change_type == watchfiles.Change.added:
                toolbox_events.send_event("file.created", {"path": str(file_path)})
            elif change_type == watchfiles.Change.modified:
                toolbox_events.send_event("file.modified", {"path": str(file_path)})
            elif change_type == watchfiles.Change.deleted:
                toolbox_events.send_event("file.deleted", {"path": str(file_path)})
