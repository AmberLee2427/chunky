# Chunky v2.0.0 — Implementation Spec

This document describes all changes required for the `chunky-files` 2.0.0 release.
It was written for a fresh implementation agent and covers every feature, bug fix,
and breaking change needed before nancy-brain can upgrade.

---

## Background

Chunky 1.0 established the pipeline and chunker infrastructure. A live audit of the
nancy-brain knowledge base revealed several problems with retrieval quality that all
trace back to chunking:

- `max_chars` is defined in `ChunkerConfig` but **never read or enforced** by any chunker.
- The sliding-window window (80 lines, 10 overlap) is far too large for embedding models
  like `all-MiniLM-L6-v2` (≈256-token context); the tokenizer silently truncates chunks,
  so most of the text in each chunk is never embedded.
- `MarkdownHeadingChunker` finds section boundaries correctly but leaves oversized sections
  as single chunks with no secondary split.
- There is no chunker for `.rst` files. They fall through to the 80-line sliding window,
  losing all structural information from Sphinx-style headings and directives.
- There is no chunker for nb4llm-converted notebooks (`.nb.txt`). They also fall through
  to the sliding window, splitting mid-cell.
- The `ChunkerRegistry` only handles single-suffix keys (`.txt`, `.md`, …). Compound
  extensions like `.nb.txt` cannot be registered.
- Tiny junk chunks (logo README, one-line RST `.. include::` stubs) enter the index
  because there is no minimum-size enforcement inside chunkers.

---

## Versioning

Bump `version` in `pyproject.toml` and `src/chunky/__about__.py` to `2.0.0`.
This is a major bump because the `ChunkerConfig` field defaults change (breaking for
any caller that relied on the old numeric defaults) and the `ChunkerRegistry` API
gains a new compound-extension feature.

---

## Change 1 — Enforce `max_chars` in every chunker

### Problem
`ChunkerConfig.max_chars` has been dead since day one.

### Required behaviour
After a chunker produces its natural segments (heading sections, AST nodes, paragraph
groups, etc.), any segment whose `len(text) > config.max_chars` must be split further
before being emitted. The secondary split strategy should be:

1. Try blank-line boundaries within the oversized segment.
2. If no blank lines, use sentence-ending punctuation (`.\n`, `!\n`, `?\n`).
3. Final fallback: sliding window over the segment using `config.lines_per_chunk`.

This secondary split must never produce an empty chunk or a chunk longer than
`max_chars` (unless a single physical line already exceeds `max_chars`, in which
case that line is emitted as-is).

### Implementation notes
- Add a module-level helper `_secondary_split(lines, max_chars)` in `_common.py` that
  implements the three-stage logic above and returns a list of `(start_line, end_line)`
  tuples.
- Call it in every chunker that currently builds segment lists before emitting:
  `MarkdownHeadingChunker`, `PythonSemanticChunker`, `PlainTextChunker`,
  `JSONYamlChunker`, `FortranChunker`, and the new `RSTChunker` /
  `NotebookChunker` (see below).
- `SlidingWindowChunker` already respects `lines_per_chunk` but should also hard-stop
  at `max_chars` by reducing the effective window: compute
  `effective_window = min(lines_per_chunk, max_chars // avg_line_len)` where
  `avg_line_len` is calculated from the first 20 lines of the document (floor at 1).
- The `make_chunk` helper in `_common.py` does **not** need to know about `max_chars`;
  the enforcement happens before `make_chunk` is called.

### Updated `ChunkerConfig` defaults
Change the defaults in `src/chunky/types.py` to values that match the typical
embedding model window:

```python
max_chars: int = 1000      # was 2000
lines_per_chunk: int = 40  # was 120 (note: the build script was already using 80)
line_overlap: int = 5      # was 20
```

---

## Change 2 — `ChunkerRegistry`: compound extension support

### Problem
`registry.get(path)` resolves only `path.suffix`. A file named `notebook.nb.txt` has
`suffix == ".txt"` and gets the plain-text chunker instead of a dedicated notebook
chunker.

### Required behaviour
Before falling back to a single-suffix lookup, the registry should check whether the
**last two suffixes joined** (e.g. `.nb.txt`) match a registered key. Priority order:

1. Compound key `path.suffixes[-2] + path.suffixes[-1]` (e.g. `.nb.txt`) — if
   registered.
2. Single suffix `path.suffix` (e.g. `.txt`) — existing behaviour.
3. Fallback chunker.

### Implementation notes
- Update `ChunkerRegistry._normalize` and `ChunkerRegistry.get` in `registry.py`.
- `register()` already accepts a list of extension strings; allow strings that contain
  an interior dot (e.g. `"nb.txt"`) — normalise by stripping any leading dot so the
  key stored in `_registry` is `"nb.txt"`.
- No API-breaking changes to `register()`'s signature are needed.

### Registration
In `src/chunky/chunkers/__init__.py`, register `NotebookChunker` (see Change 4) for
`["nb.txt"]`.

---

## Change 3 — `RSTChunker`

### What it is
A new chunker for reStructuredText files (`.rst`). RST is the dominant documentation
format in scientific Python (Sphinx) and makes up a large fraction of the nancy-brain
knowledge base.

### Section detection rules
RST headings are defined by an underline (and optional overline) of non-alphanumeric
punctuation characters at least as long as the title line. The common characters are
`= - ~ ^ " ' ` # * + :`. A line qualifies as a section boundary if:

1. The next line (underline) consists of a single repeated punctuation character,
   **or** the previous line also consists of the same repeated character (overline +
   underline style).
2. The underline is at least as long as the title text.

Chunking rules:
- Each detected section (from its heading line to the line before the next heading)
  becomes a candidate chunk.
- Any introductory content before the first heading is a separate candidate chunk
  (same as `MarkdownHeadingChunker`).
- Apply `_secondary_split` to any candidate chunk that exceeds `max_chars`.
- Fall back to `SlidingWindowChunker` if no sections are found.

### Special RST directives to respect
When falling back or doing a secondary split, prefer not to split inside a directive
block (lines that begin with `.. ` or are part of the indented body of a directive).
This is a best-effort heuristic: avoid splitting on a line that is part of an
indented directive body if a blank line exists nearby.

### Metadata
Set `chunk_type: "rst"` in each chunk's metadata.

### Registration
Register in `src/chunky/chunkers/__init__.py`:
```python
DEFAULT_REGISTRY.register(["rst"], _RST_CHUNKER)
```

---

## Change 4 — `NotebookChunker`

### What it is
A new chunker for nb4llm-converted notebook files (`.nb.txt`). The nb4llm tool
converts `.ipynb` files to a Markdown-like fenced text format with explicit cell
boundaries:

```
# notebook_name.ipynb

```markdown
<markdown cell content>
```

```python
<code cell content>
```
```

### Chunking strategy
Group cells into chunks such that each chunk contains related context — ideally a
markdown cell followed by the code cell(s) it describes. Algorithm:

1. Split the document on cell-fence boundaries (lines matching ` ```python` or
   ` ```markdown` at column 0, followed eventually by a closing ` ``` `).
2. Build a sequence of `(cell_type, lines)` tuples.
3. Merge adjacent cells into chunks:
   - Start a new chunk on each markdown cell.
   - Append following code cell(s) to the current markdown chunk until the combined
     text exceeds `max_chars` or a new markdown cell is encountered.
   - If two consecutive markdown cells appear (no code between them), merge them.
4. Apply `_secondary_split` to any chunk that still exceeds `max_chars`.
5. Fall back to `MarkdownHeadingChunker` (not `SlidingWindowChunker`) if no
   cell fences are found — nb4llm output can sometimes just be clean Markdown.

### Metadata
Set `chunk_type: "notebook"` in each chunk's metadata, plus `cell_types: list[str]`
indicating which cell types are present (e.g. `["markdown", "python"]`).

### Registration
Register in `src/chunky/chunkers/__init__.py` using the compound extension (requires
Change 2 first):
```python
DEFAULT_REGISTRY.register(["nb.txt"], _NOTEBOOK_CHUNKER)
```

---

## Change 5 — `MarkdownHeadingChunker`: secondary split for oversized sections

With Change 1 in place the generic `_secondary_split` helper handles this
automatically. The only change specific to `MarkdownHeadingChunker` is:

- After `_merge_small_sections`, iterate over the candidate segments and call
  `_secondary_split` on any segment whose content length exceeds `config.max_chars`.
- Replace the single segment with the list returned by `_secondary_split`.

No other logic changes.

---

## Change 6 — `PythonSemanticChunker`: large class body handling

Currently a class with a long body is emitted as a single chunk from `end_lineno` of
the previous node to `end_lineno` of the class node. If this chunk exceeds `max_chars`,
apply `_secondary_split`. No other changes to the Python chunker.

---

## Tests required

All existing tests must continue to pass. Add the following new test cases in
`tests/`:

### `test_max_chars_enforcement.py`
- For each chunker (`Markdown`, `Python`, `PlainText`, `YAML`, `Fortran`, `RST`,
  `Notebook`, `SlidingWindow`): verify that with `max_chars=200`, no emitted chunk
  has `len(chunk.text) > 200` (except single-line-exceeds-limit edge case).
- Verify the secondary split falls back to sliding window correctly when no blank
  lines exist.

### `test_rst_chunker.py`
- Document with multiple `===`-underlined sections → one chunk per section.
- Document with overline+underline headings → correctly detected.
- Document with no headings → falls back to sliding window.
- Exceeds `max_chars` → secondary split applied.
- Directive block not split mid-body (best effort).

### `test_notebook_chunker.py`
- Standard nb4llm output → markdown+code pairs grouped correctly.
- Large code cell → secondary split.
- No cell fences → falls back to `MarkdownHeadingChunker`.
- `cell_types` metadata populated correctly.

### `test_registry_compound.py`
- `registry.get(Path("foo.nb.txt"))` returns `NotebookChunker` when registered as
  `"nb.txt"`.
- `registry.get(Path("foo.txt"))` still returns plain-text chunker.
- Registering `"txt"` and `"nb.txt"` independently does not conflict.

### Update existing tests
- Update default values (`lines_per_chunk`, `line_overlap`, `max_chars`) in any test
  that hard-codes the old defaults (120/20/2000).

---

## Changelog entry

Add to `CHANGELOG.md` under `[2.0.0]`:

```
### Breaking changes
- `ChunkerConfig` defaults changed: `max_chars` 2000→1000, `lines_per_chunk` 120→40,
  `line_overlap` 20→5.
- `ChunkerRegistry` compound-extension lookups now take priority over single-suffix
  lookups for paths with two suffixes.

### Added
- `RSTChunker`: section-aware chunker for reStructuredText files, registered for `.rst`.
- `NotebookChunker`: cell-aware chunker for nb4llm `.nb.txt` files, registered for
  `.nb.txt` via compound extension support.
- `ChunkerRegistry` compound extension support (e.g. `"nb.txt"`).
- `_secondary_split` helper in `_common.py` enforces `max_chars` via blank-line,
  sentence, then sliding-window fallback.

### Fixed
- `max_chars` was defined in `ChunkerConfig` but never enforced; all chunkers now
  respect it.
- `MarkdownHeadingChunker` and `PythonSemanticChunker` no longer emit chunks that
  exceed `max_chars`.
- `SlidingWindowChunker` reduces effective window when `max_chars` would be exceeded
  at the default `lines_per_chunk`.
```

---

## What nancy-brain will do after the upgrade

Once `chunky-files>=2.0.0` is installed:

- `.rst` files automatically routed to `RSTChunker` via `DEFAULT_REGISTRY`.
- `.nb.txt` files automatically routed to `NotebookChunker` via compound extension.
- All chunks capped at 1000 chars by default (tunable via `CHUNKY_MAX_CHARS`).
- The build script's `chunk_config` already has new defaults (40 lines, 5 overlap,
  1000 chars) committed in nancy-brain — these match the new `ChunkerConfig` defaults.
- A full KB rebuild is required after upgrading (embeddings are not reusable across
  chunk-boundary changes).

---

## Implementation notes (agent)

- `_secondary_split` remains callable as `_secondary_split(lines, max_chars)` but now
  supports keyword-only options (`lines_per_chunk`, `avoid_boundaries`) so chunkers can
  preserve per-config window behavior and RST directive-aware split preferences.
- For overline+underline RST headings, emitted section chunks start at the overline
  marker line to keep the full heading block (`overline/title/underline`) in one chunk
  and avoid orphan preface lines.
