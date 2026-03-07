"""Pipeline-specific behavior tests."""

from __future__ import annotations

from pathlib import Path

from chunky.core import Chunker
from chunky.pipeline import ChunkPipeline
from chunky.registry import ChunkerRegistry
from chunky.types import Chunk, ChunkerConfig, Document


class _DummyChunker(Chunker):
    def chunk(self, document: Document, config: ChunkerConfig) -> list[Chunk]:
        if document.path.name == "a.txt":
            return [
                Chunk(
                    chunk_id="a#chunk-0000",
                    text="alpha paragraph with enough text",
                    source_document="a.txt",
                ),
                Chunk(chunk_id="a#chunk-0001", text="x", source_document="a.txt"),
            ]
        if document.path.name == "b.txt":
            return [
                Chunk(
                    chunk_id="b#chunk-0000",
                    text="beta paragraph with enough text",
                    source_document="b.txt",
                )
            ]
        return []


def test_multiple_documents_not_mixed() -> None:
    registry = ChunkerRegistry()
    registry.register("txt", _DummyChunker())

    pipeline = ChunkPipeline(registry=registry)
    docs = [
        Document(path=Path("a.txt"), content="unused"),
        Document(path=Path("b.txt"), content="unused"),
    ]

    chunks = pipeline.chunk_documents(docs, config=ChunkerConfig(min_chunk_chars=5))

    assert len(chunks) == 2
    assert chunks[0].source_document == "a.txt"
    assert chunks[0].text.endswith("\nx")
    assert chunks[1].source_document == "b.txt"
    assert chunks[1].text == "beta paragraph with enough text"
