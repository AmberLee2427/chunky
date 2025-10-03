"""Tests for language-aware chunkers introduced in phase 2."""

from __future__ import annotations

from pathlib import Path
import textwrap

from chunky import ChunkPipeline, ChunkerConfig


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_python_chunker_splits_top_level_defs(tmp_path: Path) -> None:
    source = textwrap.dedent(
        '''
        """Module docstring."""
        from math import sqrt

        def first():
            return sqrt(4)

        class Second:
            def method(self):
                return 42

        third = 3
        '''
    ).strip()
    path = _write(tmp_path / "module.py", source)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path, config=ChunkerConfig(lines_per_chunk=50))

    assert len(chunks) >= 3
    assert chunks[0].metadata.get("chunk_type") == "python"
    titles = [chunk.text.strip().splitlines()[0] for chunk in chunks if chunk.text.strip()]
    assert any(line.startswith("def first") for line in titles)
    assert any(line.startswith("class Second") for line in titles)


def test_markdown_chunker_groups_by_heading(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        Intro paragraph.

        # Heading One

        Details for one.

        ## Subheading

        More details.

        # Heading Two

        Final section.
        """
    ).strip()
    path = _write(tmp_path / "notes.md", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    assert len(chunks) == 4
    assert all(chunk.metadata.get("chunk_type") == "markdown" for chunk in chunks)
    assert chunks[0].metadata["line_start"] == 1  # intro captured separately


def test_json_chunker_splits_top_level_keys(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        {
          "alpha": {"value": 1},
          "beta": [1, 2, 3]
        }
        """
    ).strip()
    path = _write(tmp_path / "config.json", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    assert len(chunks) == 2
    kinds = {chunk.metadata.get("chunk_type") for chunk in chunks}
    assert kinds == {"json_object"}


def test_yaml_chunker_handles_top_level_sections(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        first:
          value: 1
        second:
          - a
          - b
        """
    ).strip()
    path = _write(tmp_path / "config.yaml", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    assert len(chunks) == 2
    assert all(chunk.metadata.get("chunk_type") == "yaml_item" for chunk in chunks)


def test_plain_text_chunker_uses_paragraphs(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        First paragraph.
        still here.

        Second paragraph.

        Third.
        """
    ).strip()
    path = _write(tmp_path / "notes.txt", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path, config=ChunkerConfig(lines_per_chunk=2))

    assert len(chunks) == 3
    assert all(chunk.metadata.get("chunk_type") == "text" for chunk in chunks)


def test_fallback_for_invalid_json(tmp_path: Path) -> None:
    path = _write(tmp_path / "broken.json", "{not: valid}")
    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path, config=ChunkerConfig(lines_per_chunk=3))

    assert chunks[0].text
    assert chunks[0].metadata.get("chunk_type") != "json_object"
