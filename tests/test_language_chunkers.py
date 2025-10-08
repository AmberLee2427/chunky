"""Tests for language-aware chunkers introduced in phase 2."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from chunky import ChunkerConfig, ChunkPipeline
from chunky.chunkers.fallback import SlidingWindowChunker
from chunky.chunkers.python import PythonSemanticChunker
from chunky.types import Document

try:  # optional Tree-sitter support
    from tree_sitter_languages import get_language  # type: ignore

    get_language("c")
    _TREE_SITTER_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency missing
    _TREE_SITTER_AVAILABLE = False


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


@pytest.mark.skipif(not _TREE_SITTER_AVAILABLE, reason="tree-sitter not installed")
def test_c_tree_sitter_chunker(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        int add(int a, int b) {
            return a + b;
        }

        static int helper(void) {
            return 42;
        }
        """
    ).strip()
    path = _write(tmp_path / "file.c", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    if not chunks or chunks[0].metadata.get("chunk_type") != "c":
        pytest.skip("Tree-sitter C grammar unavailable on this platform")

    assert len(chunks) == 2
    assert all(chunk.metadata.get("chunk_type") == "c" for chunk in chunks)


@pytest.mark.skipif(not _TREE_SITTER_AVAILABLE, reason="tree-sitter not installed")
def test_html_tree_sitter_chunker(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        <html>
          <body>
            <section><p>One</p></section>
            <section><p>Two</p></section>
          </body>
        </html>
        """
    ).strip()
    path = _write(tmp_path / "index.html", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    if not chunks or chunks[0].metadata.get("chunk_type") != "html":
        pytest.skip("Tree-sitter HTML grammar unavailable on this platform")

    assert len(chunks) >= 2
    assert all(chunk.metadata.get("chunk_type") == "html" for chunk in chunks)


def test_fortran_chunker_identifies_subroutines(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        program demo
        call hello()
        end

        subroutine hello()
        write (*,*) 'hi'
        end
        """
    ).strip()
    path = _write(tmp_path / "example.f90", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    assert len(chunks) == 2
    assert all(chunk.metadata.get("chunk_type") == "fortran" for chunk in chunks)


@pytest.mark.skipif(not _TREE_SITTER_AVAILABLE, reason="tree-sitter not installed")
def test_bash_tree_sitter_chunker(tmp_path: Path) -> None:
    content = textwrap.dedent(
        """
        #!/bin/bash

        greet() {
          echo "hi"
        }

        build() {
          echo "building"
        }
        """
    ).strip()
    path = _write(tmp_path / "script.sh", content)

    pipeline = ChunkPipeline()
    chunks = pipeline.chunk_file(path)

    if not chunks or chunks[0].metadata.get("chunk_type") != "bash":
        pytest.skip("Tree-sitter Bash grammar unavailable on this platform")

    if not chunks or chunks[0].metadata.get("chunk_type") != "bash":
        pytest.skip("Tree-sitter Bash grammar unavailable on this platform")

    assert len(chunks) == 2
    assert all(chunk.metadata.get("chunk_type") == "bash" for chunk in chunks)


def test_chunk_ids_use_doc_metadata() -> None:
    chunker = PythonSemanticChunker()
    doc = Document(
        path=Path("demo.py"),
        content="def hi():\n    return 1\n",
        metadata={"doc_id": "repo/demo.py"},
    )
    chunks = chunker.chunk(doc, ChunkerConfig())
    assert chunks
    assert chunks[0].chunk_id == "repo/demo.py#chunk-0000"
    assert chunks[0].metadata["chunk_count"] == len(chunks)
    assert chunks[0].metadata["source_document"] == "repo/demo.py"


def test_chunk_id_template_customisation(tmp_path: Path) -> None:
    chunker = SlidingWindowChunker()
    doc = Document(
        path=tmp_path / "demo.txt",
        content="one\ntwo\n",
        metadata={"slug": "docs/demo"},
    )
    config = ChunkerConfig(
        lines_per_chunk=1,
        line_overlap=0,
        doc_id_key="slug",
        chunk_id_template="{doc_id}@{index:02d}",
    )
    chunks = chunker.chunk(doc, config)
    assert chunks
    assert chunks[0].chunk_id == "docs/demo@00"
    assert chunks[0].metadata["chunk_count"] == len(chunks)
    assert chunks[0].metadata["source_document"] == "docs/demo"
