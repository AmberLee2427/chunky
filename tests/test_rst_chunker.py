"""Tests for the RST-aware chunker."""

from __future__ import annotations

import textwrap
from pathlib import Path

from chunky.chunkers.rst import RSTChunker
from chunky.types import Chunk, ChunkerConfig, Document


def _assert_limit(chunks: list[Chunk], limit: int) -> None:
    for chunk in chunks:
        lines = chunk.text.splitlines()
        if len(lines) == 1 and len(lines[0]) > limit:
            continue
        assert len(chunk.text) <= limit


def test_rst_underlined_sections_chunked_by_section() -> None:
    content = textwrap.dedent(
        """
        First Section
        =============

        Intro text.

        Second Section
        ==============

        More text.
        """
    ).strip()
    chunker = RSTChunker()
    chunks = chunker.chunk(
        Document(path=Path("guide.rst"), content=content),
        ChunkerConfig(max_chars=1000, lines_per_chunk=20, line_overlap=0),
    )

    assert len(chunks) == 2
    assert chunks[0].text.splitlines()[0] == "First Section"
    assert chunks[1].text.splitlines()[0] == "Second Section"
    assert all(chunk.metadata.get("chunk_type") == "rst" for chunk in chunks)


def test_rst_overline_headings_are_detected() -> None:
    content = textwrap.dedent(
        """
        =====
        Alpha
        =====

        Body A.

        ----
        Beta
        ----

        Body B.
        """
    ).strip()
    chunker = RSTChunker()
    chunks = chunker.chunk(
        Document(path=Path("overline.rst"), content=content),
        ChunkerConfig(max_chars=1000, lines_per_chunk=20, line_overlap=0),
    )

    assert len(chunks) == 2
    assert "Alpha" in chunks[0].text
    assert "Beta" in chunks[1].text


def test_rst_no_headings_falls_back_to_sliding_window() -> None:
    content = "\n".join(f"line {idx}" for idx in range(1, 10))
    chunker = RSTChunker()
    chunks = chunker.chunk(
        Document(path=Path("plain.rst"), content=content),
        ChunkerConfig(max_chars=1000, lines_per_chunk=3, line_overlap=0),
    )

    assert len(chunks) == 3
    assert chunks[0].metadata["line_start"] == 1
    assert chunks[0].metadata["line_end"] == 3
    assert all(chunk.metadata.get("chunk_type") == "rst" for chunk in chunks)


def test_rst_applies_secondary_split_when_section_exceeds_max_chars() -> None:
    body = "\n".join("Sentence that ends cleanly." for _ in range(60))
    content = f"Section\n=======\n{body}\n"
    chunker = RSTChunker()
    chunks = chunker.chunk(
        Document(path=Path("large.rst"), content=content),
        ChunkerConfig(max_chars=120, lines_per_chunk=6, line_overlap=0),
    )

    assert len(chunks) > 1
    _assert_limit(chunks, 120)
    assert all(chunk.metadata.get("chunk_type") == "rst" for chunk in chunks)


def test_rst_directive_body_not_split_mid_block_best_effort() -> None:
    content = textwrap.dedent(
        """
        API
        ===

        .. code-block:: python

           print("line 1")
           print("line 2")
           print("line 3")
           print("line 4")
           print("line 5")

        Narrative text. Narrative text. Narrative text.
        Narrative text. Narrative text. Narrative text.
        """
    ).strip()
    chunker = RSTChunker()
    chunks = chunker.chunk(
        Document(path=Path("directive.rst"), content=content),
        ChunkerConfig(max_chars=190, lines_per_chunk=5, line_overlap=0),
    )

    markers = [f'print("line {idx}")' for idx in range(1, 6)]
    for chunk in chunks:
        present = [marker in chunk.text for marker in markers]
        assert not (any(present) and not all(present))
