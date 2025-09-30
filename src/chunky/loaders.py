"""Document loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .types import Document


class DocumentLoader(Protocol):
    """Protocol for converting files into :class:`Document` instances."""

    def load(self, path: Path) -> Document:
        ...


class FileSystemLoader:
    """Loader that reads text files from disk."""

    def load(self, path: Path) -> Document:
        content = path.read_text(encoding="utf-8")
        return Document(path=path, content=content)


DEFAULT_LOADER = FileSystemLoader()


__all__ = ["DocumentLoader", "FileSystemLoader", "DEFAULT_LOADER"]
