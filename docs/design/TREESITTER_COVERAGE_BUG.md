# Bug Report: TreeSitterChunker silently drops non-function content

## Summary

The C++ (and C/HTML/Bash) tree-sitter chunker only captures `function_definition`
nodes. All other top-level content — `#include` directives, class/struct definitions,
global variables, namespace blocks, and any code between function bodies — is
**silently dropped**. No fallback, no warning, no coverage.

## Reproduction

```python
import sys; sys.path.insert(0, "src")
from chunky import ChunkPipeline, ChunkerConfig
from pathlib import Path

cpp_file = Path("docs/design/test_data/MulensModel/source/VBBL/VBBinaryLensingLibrary.cpp")
chunks = ChunkPipeline().chunk_file(cpp_file, config=ChunkerConfig(max_chars=2000))

total_file_chars = cpp_file.stat().st_size          # 171,140 bytes
captured_chars   = sum(len(c.text) for c in chunks) # ~74,000 chars
print(f"{captured_chars / total_file_chars:.1%} of file captured")  # ~43%
```

Tested against `VBBinaryLensingLibrary.cpp` (5,242 lines). Only 43 % of the file
is captured. The missing 57 % includes struct definitions, global constants, helper
macros, and inter-function comments that are semantically important for retrieval.

## Root cause

The registered tree-sitter query for C++ is:

```python
TreeSitterSpec(
    language="cpp",
    query="(function_definition) @chunk",
    ...
)
```

This captures only `function_definition` nodes. Tree-sitter returns their line
spans; everything between (or before/after) those spans is never emitted.

The same problem affects the C, HTML, and Bash chunkers, which all use equally
narrow `(function_definition) @chunk` queries (HTML uses element selectors but
still misses plenty of structure).

## Expected behaviour

A chunker should emit the complete file content. Non-function spans should be
collected and emitted as separate chunks (similar to how `PythonSemanticChunker`
handles the gaps between AST nodes via its `previous_end` / segment-gap logic).

## Proposed fix

### Option A — Gap-filling in `TreeSitterChunker`

After `_select_ranges()` returns the captured function spans, compute the
*complement* spans: ranges not covered by any captured node. Emit those as
additional chunks. Pseudocode:

```python
def _fill_gaps(ranges: list[tuple[int,int]], total_lines: int) -> list[tuple[int,int]]:
    """Return spans covering everything NOT in `ranges`."""
    all_spans = []
    cursor = 0
    for start, end in sorted(ranges):
        if cursor < start:
            all_spans.append((cursor, start))
        all_spans.append((start, end))
        cursor = end
    if cursor < total_lines:
        all_spans.append((cursor, total_lines))
    return all_spans
```

Call this after `_select_ranges()` and before the chunk-building loop. The
gap spans can carry different metadata (e.g. `chunk_type: "cpp_context"`) so
callers can distinguish function bodies from surrounding context if needed.

Gap spans may be large (e.g. a 400-line class definition), so they should go
through `enforce_max_chars` like everything else.

### Option B — Broader tree-sitter queries

Extend the query to capture all top-level declarations:

```
(translation_unit
  [
    (function_definition) @chunk
    (class_specifier) @chunk
    (struct_specifier) @chunk
    (declaration) @chunk
    (preproc_include) @chunk
    (namespace_definition) @chunk
    (comment) @chunk
  ]
)
```

This is more explicit but requires tuning per language and still risks missing
edge cases. Option A is language-agnostic and guarantees 100 % coverage.

## Recommended approach

Implement **Option A** (gap-filling) inside `TreeSitterChunker.chunk()`, applied
to all languages. This is sufficient to fix the coverage bug.

Option B (broader per-language queries) is a separate quality improvement tracked
in `TODO.md`. It gives better semantic labelling of captured nodes but does not
affect coverage and can be done incrementally after A lands.

## Tests to write

Add to `tests/test_language_chunkers.py` (or a new `tests/test_treesitter.py`):

| Test | Assertion |
|---|---|
| `test_cpp_full_coverage` | Sum of all chunk text lengths equals `len(source)` minus newline accounting; no content gap |
| `test_cpp_includes_captured` | At least one chunk text starts with `#include` |
| `test_cpp_struct_captured` | At least one chunk contains a top-level `struct` or `class` keyword |
| `test_gap_filling_no_functions` | File with zero function_definitions still emits all content (currently falls back to `SlidingWindowChunker`; with the fix, gap-fill should handle it) |
| `test_gap_between_functions` | Two functions with a global variable between them; variable appears in output |

Synthetic C++ fixture for tests (put in `tests/fixtures/sample.cpp`):

```cpp
#include <cmath>

static const double PI = 3.14159;

struct Point { double x, y; };

double dist(Point a, Point b) {
    return std::sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y));
}

// trailing comment
```

All five tests should pass with covered content; `#include`, `PI`, `Point`, and
`// trailing comment` must each appear in some chunk.

## Versioning

This is a bug fix → patch bump: `2.1.0` → `2.1.1` (or include in `2.1.0` if that
hasn't shipped yet). Add a `### Fixed` entry to the `[Unreleased]` CHANGELOG block.

## Implementation notes (2026-03-07)

- Gap chunks currently reuse the language `chunk_type` (for example `"cpp"`) rather
  than introducing `*_context` values. This keeps existing downstream filters and
  tests stable while still fixing the coverage bug.
- For this delivery, versioning follows the explicit request to perform a **minor**
  bump (`2.1.0` → `2.2.0`) even though this document originally suggested a patch bump.
