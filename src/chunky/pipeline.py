"""High-level orchestration for chunking documents."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .chunkers import SlidingWindowChunker
from .loaders import DEFAULT_LOADER, DocumentLoader
from .merge import merge_small_chunks
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
        chunks = chunker.chunk(document, config)
        return merge_small_chunks(chunks, config.min_chunk_chars)

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
            doc_chunks = chunker.chunk(document, config)
            chunks.extend(merge_small_chunks(doc_chunks, config.min_chunk_chars))
        return chunks

    def _ensure_fallback(self) -> None:
        try:
            self.registry.get(Path("__dummy__"))
        except KeyError:
            self.registry.set_fallback(SlidingWindowChunker())
