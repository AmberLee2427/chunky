"""Regression tests for max-char enforcement across all built-in chunkers."""

from __future__ import annotations

import textwrap
from pathlib import Path

from chunky.chunkers._common import _secondary_split
from chunky.chunkers.fallback import SlidingWindowChunker
from chunky.chunkers.fortran import FortranChunker
from chunky.chunkers.markdown import MarkdownHeadingChunker
from chunky.chunkers.notebook import NotebookChunker
from chunky.chunkers.python import PythonSemanticChunker
from chunky.chunkers.rst import RSTChunker
from chunky.chunkers.text import PlainTextChunker
from chunky.chunkers.yaml_json import JSONYamlChunker
from chunky.types import Chunk, ChunkerConfig, Document


def _assert_chunk_size_limit(chunks: list[Chunk], max_chars: int) -> None:
    assert chunks
    for chunk in chunks:
        lines = chunk.text.splitlines()
        if len(lines) == 1 and len(lines[0]) > max_chars:
            # single physical line exceeding max_chars is allowed
            continue
        assert len(chunk.text) <= max_chars


def test_chunker_config_defaults_v2() -> None:
    config = ChunkerConfig()
    assert config.max_chars == 1000
    assert config.lines_per_chunk == 40
    assert config.line_overlap == 5


def test_markdown_chunker_enforces_max_chars() -> None:
    content = "# Heading\n" + "\n".join("word" * 10 for _ in range(120))
    chunker = MarkdownHeadingChunker()
    chunks = chunker.chunk(
        Document(path=Path("notes.md"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=6, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_python_chunker_enforces_max_chars() -> None:
    content = textwrap.dedent(
        """
        class Big:
            def __init__(self):
        """
    ).strip()
    body = "\n".join(f"        self.value_{i} = {i}" for i in range(80))
    content = f"{content}\n{body}\n"

    chunker = PythonSemanticChunker()
    chunks = chunker.chunk(
        Document(path=Path("module.py"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=8, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_plain_text_chunker_enforces_max_chars() -> None:
    content = "\n".join("alpha beta gamma delta epsilon zeta eta theta" for _ in range(120))
    chunker = PlainTextChunker()
    chunks = chunker.chunk(
        Document(path=Path("notes.txt"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=7, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_yaml_chunker_enforces_max_chars() -> None:
    items = "\n".join(f"  - item_{idx}_with_extra_text" for idx in range(80))
    content = f"records:\n{items}\n"
    chunker = JSONYamlChunker()
    chunks = chunker.chunk(
        Document(path=Path("config.yaml"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=8, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_fortran_chunker_enforces_max_chars() -> None:
    body = "\n".join(f"  call step_{idx}()" for idx in range(90))
    content = f"subroutine run()\n{body}\nend\n"
    chunker = FortranChunker()
    chunks = chunker.chunk(
        Document(path=Path("model.f90"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=6, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_rst_chunker_enforces_max_chars() -> None:
    section = "\n".join("sentence ending." for _ in range(120))
    content = f"Section\n=======\n{section}\n"
    chunker = RSTChunker()
    chunks = chunker.chunk(
        Document(path=Path("guide.rst"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=8, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_notebook_chunker_enforces_max_chars() -> None:
    long_code = "\n".join(f"print('line {idx}')" for idx in range(120))
    content = textwrap.dedent(
        f"""
        # demo.ipynb

        ```markdown
        Intro cell.
        ```

        ```python
        {long_code}
        ```
        """
    ).strip()
    chunker = NotebookChunker()
    chunks = chunker.chunk(
        Document(path=Path("demo.nb.txt"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=7, line_overlap=0),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_sliding_window_chunker_enforces_max_chars() -> None:
    content = "\n".join("x" * 40 for _ in range(120))
    chunker = SlidingWindowChunker()
    chunks = chunker.chunk(
        Document(path=Path("fallback.data"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=40, line_overlap=5),
    )
    _assert_chunk_size_limit(chunks, 200)


def test_single_line_exceeding_limit_is_emitted_as_is() -> None:
    content = "A" * 500
    chunker = PlainTextChunker()
    chunks = chunker.chunk(
        Document(path=Path("single.txt"), content=content),
        ChunkerConfig(max_chars=200, lines_per_chunk=5, line_overlap=0),
    )

    assert len(chunks) == 1
    assert len(chunks[0].text) == 500


def test_secondary_split_uses_line_windows_when_no_blank_lines() -> None:
    lines = ["abcdefghijabcdefghij" for _ in range(12)]
    spans = _secondary_split(lines, 60, lines_per_chunk=4)

    assert spans[0] == (0, 2)
    assert all(start < end for start, end in spans)
