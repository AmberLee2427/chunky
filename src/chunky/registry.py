"""Chunker registry responsible for resolving the appropriate implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, MutableMapping

from .core import Chunker


class ChunkerRegistry:
    """Runtime registry mapping file extensions to chunkers."""

    def __init__(self) -> None:
        self._registry: MutableMapping[str, Chunker] = {}
        self._fallback: Chunker | None = None

    def register(
        self,
        extensions: Iterable[str] | str,
        chunker: Chunker,
        *,
        overwrite: bool = False,
    ) -> None:
        """Register a chunker for one or more extensions."""

        if isinstance(extensions, str):
            extensions = [extensions]

        for ext in extensions:
            key = self._normalize(ext)
            if not overwrite and key in self._registry:
                raise ValueError(f"Chunker already registered for extension '{ext}'")
            self._registry[key] = chunker

    def set_fallback(self, chunker: Chunker) -> None:
        """Set the fallback chunker used for unknown extensions."""

        self._fallback = chunker

    def get(self, path: Path) -> Chunker:
        """Return the chunker associated with the file path or the fallback."""

        suffix = self._normalize(path.suffix or "")
        chunker = self._registry.get(suffix)
        if chunker is not None:
            return chunker
        if self._fallback is None:
            raise KeyError(f"No chunker registered for {suffix!r} and no fallback configured")
        return self._fallback

    @staticmethod
    def _normalize(extension: str) -> str:
        return extension.lower().lstrip(".")


DEFAULT_REGISTRY = ChunkerRegistry()


__all__ = ["ChunkerRegistry", "DEFAULT_REGISTRY"]
