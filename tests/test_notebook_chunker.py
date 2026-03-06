"""Tests for notebook-aware chunking of nb4llm exports."""

from __future__ import annotations

import textwrap
from pathlib import Path

from chunky.chunkers.notebook import NotebookChunker
from chunky.types import Chunk, ChunkerConfig, Document


def _assert_limit(chunks: list[Chunk], limit: int) -> None:
    for chunk in chunks:
        lines = chunk.text.splitlines()
        if len(lines) == 1 and len(lines[0]) > limit:
            continue
        assert len(chunk.text) <= limit


def test_notebook_chunker_groups_markdown_and_code_cells() -> None:
    content = textwrap.dedent(
        """
        # notebook.ipynb

        ```markdown
        Intro to section one.
        ```

        ```python
        a = 1
        b = a + 2
        ```

        ```markdown
        Section two notes.
        ```

        ```python
        c = b * 3
        ```
        """
    ).strip()
    chunker = NotebookChunker()
    chunks = chunker.chunk(
        Document(path=Path("demo.nb.txt"), content=content),
        ChunkerConfig(max_chars=400, lines_per_chunk=10, line_overlap=0),
    )

    assert len(chunks) == 2
    assert all(chunk.metadata.get("chunk_type") == "notebook" for chunk in chunks)
    assert chunks[0].metadata.get("cell_types") == ["markdown", "python"]
    assert chunks[1].metadata.get("cell_types") == ["markdown", "python"]
    assert "Intro to section one." in chunks[0].text
    assert "c = b * 3" in chunks[1].text


def test_notebook_chunker_secondary_splits_large_code_cells() -> None:
    long_code = "\n".join(f"print('line {idx}')" for idx in range(120))
    content = "```markdown\nIntro\n```\n\n```python\n" + long_code + "\n```"
    chunker = NotebookChunker()
    chunks = chunker.chunk(
        Document(path=Path("big.nb.txt"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=8, line_overlap=0),
    )

    assert len(chunks) > 2
    assert any("python" in chunk.metadata.get("cell_types", []) for chunk in chunks)
    _assert_limit(chunks, 200)


def test_notebook_chunker_falls_back_to_markdown_when_no_fences() -> None:
    content = textwrap.dedent(
        """
        # Heading

        Intro paragraph.

        ## Details

        More context.
        """
    ).strip()
    chunker = NotebookChunker()
    chunks = chunker.chunk(
        Document(path=Path("plain.nb.txt"), content=content),
        ChunkerConfig(max_chars=400, lines_per_chunk=20, line_overlap=0),
    )

    assert len(chunks) >= 1
    assert all(chunk.metadata.get("chunk_type") == "notebook" for chunk in chunks)
    assert all(chunk.metadata.get("cell_types") == ["markdown"] for chunk in chunks)


def test_notebook_chunker_populates_cell_type_metadata() -> None:
    content = textwrap.dedent(
        """
        ```markdown
        First markdown block.
        ```

        ```markdown
        Second markdown block.
        ```

        ```python
        x = 1
        y = x + 1
        ```
        """
    ).strip()
    chunker = NotebookChunker()
    chunks = chunker.chunk(
        Document(path=Path("cells.nb.txt"), content=content),
        ChunkerConfig(max_chars=400, lines_per_chunk=20, line_overlap=0),
    )

    assert chunks
    assert chunks[0].metadata.get("cell_types") == ["markdown", "python"]
