# Chunky v2.1.0 — Forward-Merge Spec

This document specifies all changes required to add forward-merge of small chunks
to `chunky-files`. It was written for a fresh implementation agent.

---

## Background

Nancy-brain's knowledge-base build pipeline contained a per-chunk drop filter:
if a chunk had fewer than `MIN_CHUNK_CHARS` stripped characters, it was silently
discarded. Investigation (see `docs/design/chunk_merge_investigation.ipynb`)
showed this destroyed content like:

- module-level imports
- brief comments and decorators
- short docstrings
- structural stubs at the start or end of a file

These are not noise — they introduce the code that follows and carry real semantic
weight.  Dropping them degrades retrieval quality.

The notebook validates that a **forward-merge** strategy recovers 100 % of content
across all seven test files, while the drop approach lost 2–16 lines per file
(coverage range 68.8 %–99.4 %).

Forward-merge logic was briefly added to nancy-brain's `build_knowledge_base.py`
for validation, then removed. It belongs in chunky itself.

---

## Versioning

Bump `version` in `pyproject.toml` **and** `src/chunky/__about__.py` from `2.0.1`
to `2.1.0`. This is a minor bump because the change is:

- backward compatible (new `min_chunk_chars` field defaults to `0` = disabled),
- additive (new public function `merge_small_chunks`),
- does not break any existing call site.

---

## Change 1 — Add `min_chunk_chars` to `ChunkerConfig`

**File**: `src/chunky/types.py`

Add one new field to `ChunkerConfig`:

```python
min_chunk_chars: int = 0
```

Place it after `max_chars`.  The default `0` means "disabled" — nothing changes for
existing callers.

```python
@dataclass
class ChunkerConfig:
    max_chars: int = 1000
    min_chunk_chars: int = 0          # ← new
    lines_per_chunk: int = 40
    ...
```

---

## Change 2 — Implement `merge_small_chunks` in a new module

**File**: `src/chunky/merge.py` (new file)

```python
"""Forward-merge utility for small chunks."""

from __future__ import annotations

import dataclasses
from .types import Chunk


def merge_small_chunks(chunks: list[Chunk], min_chars: int) -> list[Chunk]:
    """Merge chunks smaller than *min_chars* into their successor.

    Tiny chunks are accumulated in a carry buffer and prepended to the next
    chunk whose stripped text meets the minimum.  If the last chunk(s) are
    still below the threshold after the loop, they are appended to the
    preceding output chunk.

    Parameters
    ----------
    chunks:
        The chunk list to merge.  Chunking is per-document so all chunks
        should share the same ``source_document``.
    min_chars:
        Minimum number of stripped characters a chunk must have to be emitted
        as-is.  Pass ``0`` to skip merging entirely (no-op fast path).

    Returns
    -------
    list[Chunk]
        New list; original chunks are not mutated.
    """

    if min_chars <= 0 or not chunks:
        return chunks

    result: list[Chunk] = []
    carry: list[str] = []

    for chunk in chunks:
        if len(chunk.text.strip()) < min_chars:
            carry.append(chunk.text)
        else:
            if carry:
                merged_text = "\n".join(carry) + "\n" + chunk.text
                carry = []
                chunk = dataclasses.replace(chunk, text=merged_text)
            result.append(chunk)

    # Trailing tiny chunks — append to the last emitted chunk if possible.
    if carry:
        if result:
            last = result[-1]
            result[-1] = dataclasses.replace(
                last, text=last.text + "\n" + "\n".join(carry)
            )
        else:
            # Edge case: every chunk was tiny; emit each one anyway so
            # content is never silently dropped.
            result.extend(chunks)

    return result
```

### Algorithm notes

- **Forward, not backward**: imports, decorators, and brief comments all
  *introduce* the code that follows.  Prepending carry to the successor keeps
  the semantic unit together.
- **Edge case — all tiny**: return all chunks unchanged rather than silently
  dropping everything.  (The single-chunk-file case falls here too.)
- **Chunk IDs**: `dataclasses.replace` copies every field, so `chunk_id`,
  `source_document`, and `metadata` from the *successor* chunk are preserved.
  That is intentional — the merged chunk takes the identity of the chunk that
  "absorbs" the carry.

---

## Change 3 — Call `merge_small_chunks` in `ChunkPipeline`

**File**: `src/chunky/pipeline.py`

Import the new function and call it in both public methods, per-document so
chunk IDs stay within one document's namespace.

```python
from .merge import merge_small_chunks
```

In `chunk_file`:

```python
def chunk_file(self, path: Path | str, *, config: Optional[ChunkerConfig] = None) -> list[Chunk]:
    config = config or ChunkerConfig()
    document = self.loader.load(Path(path))
    chunker = self.registry.get(document.path)
    chunks = chunker.chunk(document, config)
    return merge_small_chunks(chunks, config.min_chunk_chars)
```

In `chunk_documents`:

```python
def chunk_documents(self, documents: list[Document], *, config: Optional[ChunkerConfig] = None) -> list[Chunk]:
    config = config or ChunkerConfig()
    chunks: list[Chunk] = []
    for document in documents:
        chunker = self.registry.get(document.path)
        doc_chunks = chunker.chunk(document, config)
        chunks.extend(merge_small_chunks(doc_chunks, config.min_chunk_chars))
    return chunks
```

Note: merge is applied **per-document** so carry never crosses document
boundaries.

---

## Change 4 — Export from package

**File**: `src/chunky/__init__.py`

Add `merge_small_chunks` to the public API so callers can use it standalone
without going through the pipeline:

```python
from .merge import merge_small_chunks
```

Include it in `__all__` if the file uses one.

---

## Tests

**File**: `tests/test_merge.py` (new file)

Write a test module covering every meaningful branch.  Use only stdlib and the
chunky types — no real files or pipeline needed.

### Helper

```python
def make_chunk(text: str, chunk_id: str = "doc#chunk-0001") -> Chunk:
    return Chunk(chunk_id=chunk_id, text=text, source_document="doc.py")
```

### Required test cases

| Test name | Scenario | Expected result |
|---|---|---|
| `test_noop_when_min_chars_zero` | `min_chars=0` | Input list returned unchanged (identity) |
| `test_noop_empty_list` | Empty input | `[]` |
| `test_all_large_chunks_unchanged` | All chunks above threshold | Same list returned |
| `test_single_tiny_chunk_not_dropped` | One chunk below threshold | That one chunk returned (no silent drop) |
| `test_leading_tiny_merged_into_successor` | Two chunks: `[tiny, large]` | One chunk whose text is `tiny\nlarge` |
| `test_trailing_tiny_appended_to_predecessor` | Two chunks: `[large, tiny]` | One chunk whose text is `large\ntiny` |
| `test_consecutive_tiny_chunks` | `[tiny, tiny, large]` | One chunk: `tiny\ntiny\nlarge` |
| `test_gap_tiny_chunks_target_correct_successor` | `[large, tiny, tiny, large]` | Two chunks: first large unchanged; second is `tiny\ntiny\nlarge` |
| `test_all_tiny_chunks_returned` | All chunks below threshold | All original chunks returned (none dropped) |
| `test_chunk_id_from_successor` | Leading tiny + large | Merged chunk keeps the large chunk's `chunk_id` |
| `test_multiple_documents_not_mixed` | Call `chunk_documents` with two docs | Carry does not cross document boundary |

The last test belongs in `tests/test_pipeline.py` — assert that `chunk_documents`
with `min_chunk_chars > 0` produces the right number of chunks per doc and that
no text from doc-A appears in doc-B's chunks.

---

## CHANGELOG

Add a new `[2.1.0]` entry in `CHANGELOG.md`.  Keep the existing `[Unreleased]`
section for future work; insert `[2.1.0]` directly above the `[2.0.1]` block.
Use the same "Keep a Changelog" section order (Added / Changed / Fixed / Removed).

```markdown
## [2.1.0] - YYYY-MM-DD

### Added
- `ChunkerConfig.min_chunk_chars` field (default `0` = disabled).  When set to a
  positive integer, chunks with fewer stripped characters are forward-merged into
  their successor rather than dropped.
- `merge_small_chunks(chunks, min_chars)` public utility function in
  `chunky.merge`, also exported from the top-level `chunky` package.
- `ChunkPipeline.chunk_file` and `ChunkPipeline.chunk_documents` now apply
  forward-merge automatically when `config.min_chunk_chars > 0`.
```

---

## Summary of files to create / edit

| File | Action |
|---|---|
| `src/chunky/__about__.py` | Bump `__version__` to `"2.1.0"` |
| `pyproject.toml` | Bump `version` to `"2.1.0"` |
| `src/chunky/types.py` | Add `min_chunk_chars: int = 0` to `ChunkerConfig` |
| `src/chunky/merge.py` | **Create** with `merge_small_chunks` implementation |
| `src/chunky/__init__.py` | Import and export `merge_small_chunks` |
| `src/chunky/pipeline.py` | Import `merge_small_chunks`; apply in `chunk_file` and `chunk_documents` |
| `tests/test_merge.py` | **Create** with all unit tests listed above |
| `tests/test_pipeline.py` | Add cross-document carry test |
| `CHANGELOG.md` | Add `[2.1.0]` entry |
