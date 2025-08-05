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


mcp = FastMCP("obsidian-mcp", lifespan=app_lifespan)


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


@mcp.tool(description="Read a markdown file from the Obsidian vault with metadata")
def read_document(path: str, ctx: Context) -> Document:
    """Read a markdown file from the vault with metadata"""
    vault_path = ctx.request_context.lifespan_context.vault_path
    file_path = (vault_path / path).resolve()

    if not is_safe_path(file_path, vault_path) or not file_path.exists():
        raise ValueError("File not found or not accessible")

    content = file_path.read_text(encoding="utf-8")
    info = get_file_info(file_path, vault_path)

    return Document(content=content, **info.model_dump())


@mcp.tool(description="Read an image from the Obsidian vault")
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


@mcp.tool(description="Get the location and file format of the daily notes")
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


@mcp.tool(description="List markdown files in the Obsidian vault with metadata")
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
