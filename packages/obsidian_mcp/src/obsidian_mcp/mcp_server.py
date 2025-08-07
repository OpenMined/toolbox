import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP, Image
from mcp.server.stdio import stdio_server
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

OBSIDIAN_SETTINGS_FOLDER = ".obsidian"
OBSIDIAN_DAILY_NOTES_SETTINGS = "daily-notes.json"


@dataclass
class AppContext:
    """Application context with vault path."""

    vault_path: Path


class FileInfo(BaseModel):
    """File information structure."""

    path: str = Field(description="Relative path from vault root")
    name: str = Field(description="File name")
    size_bytes: int = Field(description="File size in bytes")
    created: datetime = Field(description="Creation time")
    modified: datetime = Field(description="Last modification time")


class Document(FileInfo):
    """Document with content and metadata."""

    content: str = Field(description="File content")


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with vault path initialization."""
    vault_env = os.getenv("OBSIDIAN_VAULT_PATH")
    if not vault_env:
        raise ValueError("OBSIDIAN_VAULT_PATH environment variable not set")

    vault_path = Path(vault_env).resolve()
    if not vault_path.is_dir():
        raise ValueError(
            f"Vault path does not exist or is not a directory: {vault_path}"
        )

    yield AppContext(vault_path=vault_path)


mcp = FastMCP(
    "obsidian-mcp",
    lifespan=app_lifespan,
)


def is_safe_path(path: Path, vault_path: Path) -> bool:
    """Check if path is within vault and not in .obsidian"""
    try:
        resolved = path.resolve()
        resolved.relative_to(vault_path)
        return ".obsidian" not in resolved.parts
    except ValueError:
        return False


def get_file_info(file_path: Path, vault_path: Path) -> FileInfo:
    """Get file information structure."""
    stat = file_path.stat()
    relative_path = file_path.relative_to(vault_path)

    return FileInfo(
        path=str(relative_path),
        name=file_path.name,
        size_bytes=stat.st_size,
        created=datetime.fromtimestamp(stat.st_ctime),
        modified=datetime.fromtimestamp(stat.st_mtime),
    )


@mcp.tool(
    description=(
        "Read a markdown file from the Obsidian vault with metadata. "
        "Simple filesystem-based operation that returns document content and file info."
    ),
    annotations=ToolAnnotations(readOnly=True),
)
def read_document(path: str, ctx: Context) -> Document:
    """Read a markdown file from the vault with metadata"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()

    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    content = file_path.read_text(encoding="utf-8")
    info = get_file_info(file_path, vault_path)

    return Document(content=content, **info.model_dump())


@mcp.tool(
    description=(
        "Read an image from the Obsidian vault. "
        "Simple filesystem-based operation that returns image data."
    )
)
def read_image(path: str, ctx: Context) -> Image:
    """Read an image from the vault"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()
    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    return Image(data=file_path.read_bytes(), path=path)


class DailyNotesSettings(BaseModel):
    folder: str = Field(
        description="Daily notes folder. If empty, daily notes are stored in root"
    )
    format: str = Field(description="Format of the daily notes files")


@mcp.tool(
    description=(
        "Get the location and file format of the daily notes. "
        "Returns None if no daily notes settings are found."
    )
)
def daily_notes_settings(ctx: Context) -> DailyNotesSettings | None:
    """Get the location and file format of the daily notes. Returns None if no daily notes settings are found."""
    vault_path = ctx.request_context.lifespan_context.vault_path
    daily_notes_settings_path = (
        vault_path / OBSIDIAN_SETTINGS_FOLDER / OBSIDIAN_DAILY_NOTES_SETTINGS
    )
    if not daily_notes_settings_path.exists():
        return None

    loaded_settings = json.loads(daily_notes_settings_path.read_text())
    return DailyNotesSettings(
        folder=loaded_settings.get("folder", "/"),
        format=loaded_settings.get("format", "YYYY-MM-DD"),
    )


@mcp.tool(
    description=(
        "Replace entire file content in the Obsidian vault. "
        "CAUTION: This is a destructive operation - use only when explicitly requested. "
        "Prefer insert_lines/remove_lines instead. "
        "Uses atomic write with temporary file and backup for safety."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def replace_entire_file(path: str, new_content: str, ctx: Context) -> None:
    """Update a markdown file in the vault"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()
    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    # Create backup and use atomic write
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        # Create backup
        backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

        # Write to temp file first
        temp_path.write_text(new_content, encoding="utf-8")

        # Atomic move
        temp_path.replace(file_path)

        # Clean up backup after successful write
        backup_path.unlink()

    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        # Restore from backup if needed
        if backup_path.exists() and not file_path.exists():
            backup_path.replace(file_path)
        elif backup_path.exists():
            backup_path.unlink()
        raise e


@mcp.tool(
    description=(
        "Insert lines at a specific position in a markdown file (1-based line numbering). "
        "CAUTION: File modification tool - use only when user explicitly requests it. "
        "Uses atomic write with temporary file and backup for safety."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def insert_lines(path: str, line_number: int, lines: list[str], ctx: Context) -> None:
    """Insert lines at a specific position (1-based line numbering)"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()
    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    current_content = file_path.read_text(encoding="utf-8")
    current_lines = current_content.splitlines(keepends=True)

    # Convert to 0-based indexing, clamp to valid range
    insert_pos = max(0, min(line_number - 1, len(current_lines)))

    # Insert new lines
    new_lines = (
        current_lines[:insert_pos]
        + [line + "\n" for line in lines]
        + current_lines[insert_pos:]
    )
    new_content = "".join(new_lines)

    # Use the safe update_file function
    replace_entire_file(path, new_content, ctx)


@mcp.tool(
    description=(
        "Remove lines from a markdown file by line range (inclusive, 1-based numbering). "
        "CAUTION: This is a destructive operation - use only when user explicitly requests it. "
        "Uses atomic write with temporary file and backup for safety."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructive=True),
)
def remove_lines(path: str, start_line: int, end_line: int, ctx: Context) -> None:
    """Remove lines from start_line to end_line (inclusive, 1-based line numbering)"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()
    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    current_content = file_path.read_text(encoding="utf-8")
    current_lines = current_content.splitlines(keepends=True)

    # Convert to 0-based indexing, validate range
    start_idx = max(0, start_line - 1)
    end_idx = min(len(current_lines), end_line)

    if start_idx >= end_idx:
        raise ValueError("Invalid line range")

    # Remove lines
    new_lines = current_lines[:start_idx] + current_lines[end_idx:]
    new_content = "".join(new_lines)

    # Use the safe update_file function
    replace_entire_file(path, new_content, ctx)


@mcp.tool(
    description=(
        "Append lines to the end of a markdown file. "
        "CAUTION: File modification tool - use only when user explicitly requests it. "
        "Uses atomic write with temporary file and backup for safety."
    )
)
def append_lines(path: str, lines: list[str], ctx: Context) -> None:
    """Append lines to the end of a markdown file"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()
    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    current_content = file_path.read_text(encoding="utf-8")

    # Ensure file ends with newline before appending
    if current_content and not current_content.endswith("\n"):
        current_content += "\n"

    # Append new lines
    new_content = current_content + "\n".join(lines) + "\n"

    # Use the safe update_file function
    replace_entire_file(path, new_content, ctx)


@mcp.tool(
    description=(
        "Replace lines in a markdown file by line range (inclusive, 1-based numbering). "
        "CAUTION: File modification tool - use only when user explicitly requests it. "
        "Uses atomic write with temporary file and backup for safety."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True),
)
def replace_lines(
    path: str, start_line: int, end_line: int, lines: list[str], ctx: Context
) -> None:
    """Replace lines in a markdown file by line range (inclusive, 1-based numbering)."""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()
    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    current_content = file_path.read_text(encoding="utf-8")
    current_lines = current_content.splitlines(keepends=True)

    # Convert to 0-based indexing, validate range
    start_idx = max(0, start_line - 1)
    end_idx = min(len(current_lines), end_line)

    if start_idx >= end_idx:
        raise ValueError("Invalid line range")

    # Replace lines
    new_lines = (
        current_lines[:start_idx]
        + [line + "\n" for line in lines]
        + current_lines[end_idx:]
    )
    new_content = "".join(new_lines)

    # Use the safe update_file function
    replace_entire_file(path, new_content, ctx)


@mcp.tool(
    description=(
        "Create a new markdown file in the Obsidian vault. "
        "CAUTION: File creation tool - use only when user explicitly requests it. "
        "Uses atomic write with temporary file for safety."
    )
)
def create_file(path: str, ctx: Context, content: str = "") -> None:
    """Create a new markdown file in the vault"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()

    if not is_safe_path(file_path, vault_path):
        raise ValueError("File path not accessible")

    if file_path.exists():
        raise ValueError(f"File already exists: {path}")

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write content atomically
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(file_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e


@mcp.tool(
    description=(
        "List markdown files in the Obsidian vault with metadata. "
        "Simple filesystem-based operation with optional filtering and sorting."
    )
)
def list_files(
    ctx: Context,
    subfolder: str = "",
    order_by: Literal["path", "name", "size", "created", "modified"] | None = None,
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = 100,
    offset: int = 0,
) -> list[FileInfo]:
    """List markdown files in the vault with metadata"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    search_path = vault_path / subfolder if subfolder else vault_path

    if not is_safe_path(search_path, vault_path):
        raise ValueError("Invalid subfolder path")

    files = []
    if search_path.exists():
        for md_file in search_path.rglob("*.md"):
            if is_safe_path(md_file, vault_path):
                files.append(get_file_info(md_file, vault_path))

    if order_by:
        files = sorted(
            files,
            key=lambda f: getattr(f, order_by),
            reverse=sort_order == "desc",
        )
    else:
        files = sorted(files, key=lambda f: f.path)

    if offset:
        files = files[offset:]
    if limit:
        files = files[:limit]
    return files


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
