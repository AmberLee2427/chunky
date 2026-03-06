"""Tests for compound-extension registry lookups."""

from __future__ import annotations

from pathlib import Path

from chunky.chunkers import DEFAULT_REGISTRY
from chunky.chunkers.fallback import SlidingWindowChunker
from chunky.chunkers.notebook import NotebookChunker
from chunky.chunkers.text import PlainTextChunker
from chunky.registry import ChunkerRegistry


def test_default_registry_handles_unknown_extension_without_pipeline() -> None:
    """DEFAULT_REGISTRY must have a fallback so callers don't need ChunkPipeline."""
    chunker = DEFAULT_REGISTRY.get(Path("mystery.unknownext"))
    assert isinstance(chunker, SlidingWindowChunker)



def test_registry_prefers_compound_extension_lookup() -> None:
    registry = ChunkerRegistry()
    text_chunker = PlainTextChunker()
    notebook_chunker = NotebookChunker()

    registry.register("txt", text_chunker)
    registry.register("nb.txt", notebook_chunker)
    registry.set_fallback(SlidingWindowChunker())

    assert registry.get(Path("foo.nb.txt")) is notebook_chunker


def test_registry_still_supports_single_suffix_lookup() -> None:
    registry = ChunkerRegistry()
    text_chunker = PlainTextChunker()
    notebook_chunker = NotebookChunker()

    registry.register("txt", text_chunker)
    registry.register("nb.txt", notebook_chunker)
    registry.set_fallback(SlidingWindowChunker())

    assert registry.get(Path("foo.txt")) is text_chunker


def test_registry_can_register_txt_and_nb_txt_without_conflict() -> None:
    registry = ChunkerRegistry()
    text_chunker = PlainTextChunker()
    notebook_chunker = NotebookChunker()

    registry.register("txt", text_chunker)
    registry.register("nb.txt", notebook_chunker)
    registry.set_fallback(SlidingWindowChunker())

    assert registry.get(Path("sample.txt")) is text_chunker
    assert registry.get(Path("sample.nb.txt")) is notebook_chunker
