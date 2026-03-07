"""Tests for forward-merge of small chunks."""

from __future__ import annotations

from chunky.merge import merge_small_chunks
from chunky.types import Chunk


def make_chunk(text: str, chunk_id: str = "doc#chunk-0001") -> Chunk:
    return Chunk(chunk_id=chunk_id, text=text, source_document="doc.py")


def test_noop_when_min_chars_zero() -> None:
    chunks = [make_chunk("alpha"), make_chunk("beta")]
    merged = merge_small_chunks(chunks, 0)
    assert merged is chunks


def test_noop_empty_list() -> None:
    assert merge_small_chunks([], 10) == []


def test_all_large_chunks_unchanged() -> None:
    chunks = [make_chunk("alpha", "doc#chunk-0000"), make_chunk("beta", "doc#chunk-0001")]
    merged = merge_small_chunks(chunks, 2)
    assert merged is chunks


def test_single_tiny_chunk_not_dropped() -> None:
    chunks = [make_chunk("x", "doc#chunk-0000")]
    merged = merge_small_chunks(chunks, 2)
    assert merged == chunks


def test_leading_tiny_merged_into_successor() -> None:
    chunks = [make_chunk("x", "doc#chunk-0000"), make_chunk("large", "doc#chunk-0001")]
    merged = merge_small_chunks(chunks, 2)
    assert len(merged) == 1
    assert merged[0].text == "x\nlarge"


def test_trailing_tiny_appended_to_predecessor() -> None:
    chunks = [make_chunk("large", "doc#chunk-0000"), make_chunk("x", "doc#chunk-0001")]
    merged = merge_small_chunks(chunks, 2)
    assert len(merged) == 1
    assert merged[0].text == "large\nx"


def test_consecutive_tiny_chunks() -> None:
    chunks = [
        make_chunk("a", "doc#chunk-0000"),
        make_chunk("b", "doc#chunk-0001"),
        make_chunk("large", "doc#chunk-0002"),
    ]
    merged = merge_small_chunks(chunks, 2)
    assert len(merged) == 1
    assert merged[0].text == "a\nb\nlarge"


def test_gap_tiny_chunks_target_correct_successor() -> None:
    chunks = [
        make_chunk("large-1", "doc#chunk-0000"),
        make_chunk("a", "doc#chunk-0001"),
        make_chunk("b", "doc#chunk-0002"),
        make_chunk("large-2", "doc#chunk-0003"),
    ]
    merged = merge_small_chunks(chunks, 2)
    assert len(merged) == 2
    assert merged[0].text == "large-1"
    assert merged[1].text == "a\nb\nlarge-2"


def test_all_tiny_chunks_returned() -> None:
    chunks = [
        make_chunk("a", "doc#chunk-0000"),
        make_chunk("b", "doc#chunk-0001"),
        make_chunk("c", "doc#chunk-0002"),
    ]
    merged = merge_small_chunks(chunks, 2)
    assert merged == chunks


def test_chunk_id_from_successor() -> None:
    chunks = [make_chunk("x", "doc#chunk-0000"), make_chunk("large", "doc#chunk-9999")]
    merged = merge_small_chunks(chunks, 2)
    assert len(merged) == 1
    assert merged[0].chunk_id == "doc#chunk-9999"
