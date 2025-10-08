"""Tests for the sliding window fallback chunker and pipeline."""

from __future__ import annotations

from pathlib import Path

from chunky.pipeline import ChunkPipeline
from chunky.types import ChunkerConfig


def _write_tmp(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_sliding_window_chunks_by_lines(tmp_path: Path) -> None:
    pipeline = ChunkPipeline()
    content = "\n".join(f"line {i}" for i in range(1, 251))
    path = _write_tmp(tmp_path, "sample.fallback", content)

    config = ChunkerConfig(lines_per_chunk=50, line_overlap=10)
    chunks = pipeline.chunk_file(path, config=config)

    # Expect ceiling((250 - 50) / (50 - 10)) + 1 => 6 chunks
    assert len(chunks) == 6
    assert chunks[0].metadata["line_start"] == 1
    assert chunks[0].metadata["line_end"] == 50
    assert chunks[-1].metadata["line_end"] == 250
    # Next chunk should overlap by 10 lines (start at 41)
    assert chunks[1].metadata["line_start"] == 41
    total = len(chunks)
    assert all(chunk.metadata["chunk_count"] == total for chunk in chunks)
    assert all("sample.fallback" in chunk.metadata["source_document"] for chunk in chunks)


def test_metadata_includes_character_offsets(tmp_path: Path) -> None:
    pipeline = ChunkPipeline()
    content = "first\nsecond\nthird\nfourth"
    path = _write_tmp(tmp_path, "chars.custom", content)

    config = ChunkerConfig(lines_per_chunk=2, line_overlap=0)
    chunks = pipeline.chunk_file(path, config=config)

    assert len(chunks) == 2
    first = chunks[0].metadata
    second = chunks[1].metadata
    assert first["span_start"] == 0
    assert content[first["span_start"] : first["span_end"]] == chunks[0].text
    assert content[second["span_start"] : second["span_end"]] == chunks[1].text
    assert chunks[0].metadata["chunk_count"] == 2


def test_max_chunks_limit(tmp_path: Path) -> None:
    pipeline = ChunkPipeline()
    content = "\n".join(f"row {i}" for i in range(40))
    path = _write_tmp(tmp_path, "limited.custom", content)

    config = ChunkerConfig(lines_per_chunk=10, line_overlap=0, max_chunks=2)
    chunks = pipeline.chunk_file(path, config=config)

    assert len(chunks) == 2
    # Last chunk stops at line 20 even though more content remains
    assert chunks[-1].metadata["line_end"] == 20


def test_fallback_handles_unknown_extension(tmp_path: Path) -> None:
    pipeline = ChunkPipeline()
    path = _write_tmp(tmp_path, "file.unknown", "one\ntwo\nthree")

    chunks = pipeline.chunk_file(path)

    assert len(chunks) == 1
    assert chunks[0].text.startswith("one")


def test_empty_file_produces_empty_chunk(tmp_path: Path) -> None:
    pipeline = ChunkPipeline()
    path = _write_tmp(tmp_path, "empty.txt", "")

    chunks = pipeline.chunk_file(path)

    assert len(chunks) == 1
    assert chunks[0].text == ""
    assert chunks[0].metadata["line_start"] == 0
    assert chunks[0].metadata["line_end"] == 0


def test_overlap_greater_than_window_is_clamped(tmp_path: Path) -> None:
    pipeline = ChunkPipeline()
    path = _write_tmp(tmp_path, "clamp.custom", "\n".join("x" for _ in range(30)))

    config = ChunkerConfig(lines_per_chunk=10, line_overlap=25)
    chunks = pipeline.chunk_file(path, config=config)

    # Overlap should clamp to window - 1, so second chunk starts at line 2
    assert chunks[1].metadata["line_start"] == 2
    assert all(chunk.text for chunk in chunks)
