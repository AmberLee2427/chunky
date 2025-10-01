"""High-level orchestration for chunking documents."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .chunkers import SlidingWindowChunker
from .loaders import DEFAULT_LOADER, DocumentLoader
from .registry import DEFAULT_REGISTRY, ChunkerRegistry
from .types import Chunk, ChunkerConfig, Document


class ChunkPipeline:
    """Pipeline that orchestrates document loading and chunking."""

    def __init__(
        self,
        *,
        registry: Optional[ChunkerRegistry] = None,
        loader: Optional[DocumentLoader] = None,
    ) -> None:
        self.registry = registry or DEFAULT_REGISTRY
        self.loader = loader or DEFAULT_LOADER
        self._ensure_fallback()

    def chunk_file(
        self,
        path: Path | str,
        *,
        config: Optional[ChunkerConfig] = None,
    ) -> list[Chunk]:
        """Chunk a file from disk."""

        config = config or ChunkerConfig()
        document = self.loader.load(Path(path))
        chunker = self.registry.get(document.path)
        return chunker.chunk(document, config)

    def chunk_documents(
        self,
        documents: list[Document],
        *,
        config: Optional[ChunkerConfig] = None,
    ) -> list[Chunk]:
        """Chunk pre-loaded documents."""

        config = config or ChunkerConfig()
        chunks: list[Chunk] = []
        for document in documents:
            chunker = self.registry.get(document.path)
            chunks.extend(chunker.chunk(document, config))
        return chunks

    def _ensure_fallback(self) -> None:
        try:
            self.registry.get(Path("__dummy__"))
        except KeyError:
            self.registry.set_fallback(SlidingWindowChunker())
