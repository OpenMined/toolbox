from datetime import datetime, timezone
from pathlib import Path

from toolbox_store.models import TBDocument


def load_from_dir(
    data_dir: Path,
    pattern: str = "*.txt",
    max_docs: int | None = None,
) -> list[TBDocument]:
    """
    Load documents from a directory.

    TODO incremental loading based on modified time/hash

    Args:
        data_dir: Directory containing documents
        pattern: Glob pattern for files to load (default: "*.txt")
        max_docs: Maximum number of documents to load (default: all)

    Returns:
        List of TBDocument objects
    """
    documents = []
    files = sorted(data_dir.glob(pattern))

    if max_docs:
        files = files[:max_docs]

    for file_path in files:
        try:
            content = file_path.read_text()
            document = TBDocument(
                content=content,
                metadata={
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "created_at": datetime.fromtimestamp(
                        file_path.stat().st_ctime, tz=timezone.utc
                    ).isoformat(),
                    "updated_at": datetime.fromtimestamp(
                        file_path.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                },
                source=f"file://{file_path.as_posix()}",
            )
            documents.append(document)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue

    return documents
