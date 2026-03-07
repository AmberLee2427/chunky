# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.1] - 2026-03-07

### Fixed
- `TreeSitterChunker` now emits uncovered line ranges between captured AST nodes,
  so C/C++/HTML/Bash chunking preserves full file coverage instead of silently
  dropping non-matching content.
- Tree-sitter language tests now validate coverage and context retention for
  includes, structs, inter-function globals, and files with no function definitions.

## [2.1.0] - 2026-03-07

### Added
- `ChunkerConfig.min_chunk_chars` field (default `0` = disabled). When set to a
  positive integer, chunks with fewer stripped characters are forward-merged into
  their successor rather than dropped.
- `merge_small_chunks(chunks, min_chars)` public utility function in
  `chunky.merge`, also exported from the top-level `chunky` package.
- `ChunkPipeline.chunk_file` and `ChunkPipeline.chunk_documents` now apply
  forward-merge automatically when `config.min_chunk_chars > 0`.

## [2.0.1] - 2026-03-06

### Fixed
- `DEFAULT_REGISTRY` had no fallback chunker set at import time. Calling
  `DEFAULT_REGISTRY.get(path)` for an unregistered extension raised `KeyError`
  unless a `ChunkPipeline` had been instantiated first. `SlidingWindowChunker`
  is now set as the fallback in `chunkers/__init__.py` alongside the other
  `register()` calls.

## [2.0.0] - 2026-03-06

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

## [1.0.0] - 2025-10-07

### Added
- Stable chunk identifiers (`<doc_id>#chunk-0000`) with configurable metadata keys/templates and per-chunk `chunk_count`/`source_document` fields.

## [0.4.0] - 2025-09-30

### Changed
- Optional `tree` extra now installs `tree-sitter==0.20.1` plus bundled grammars for consistent Tree-sitter support (C/C++/HTML/Bash).

## [0.3.0] - 2025-09-30

### Added
- Language-aware chunkers for Python, Markdown, JSON/YAML, plain text, Fortran, and Tree-sitter powered C/C++/HTML support.
- Registry bootstrap that pre-registers the built-in chunkers for common extensions.
- Unit tests covering the new chunkers and regression coverage for the sliding-window fallback.

## [0.2.2] - 2025-09-30
### Fixed
- Pinned the release workflow to `pypa/gh-action-pypi-publish@release/v1` and added a `twine check` gate, eliminating spurious "missing Name/Version" errors during automated publishes.
- Corrected the Sphinx intersphinx configuration so Read the Docs builds resolve the Python inventory without manual tweaks.

## [0.2.1] - 2025-09-30

### Changed
- Renamed the published distribution to `chunky-files` and refreshed packaging metadata for the new name.

### Fixed
- Ensured `pyproject.toml` ships in the sdist include list to keep build metadata intact across platforms.

## [0.2.0] - TBD
### Added
- Changelog (`CHANGELOG.md`; this file).
- Release process section added to the existing `README.md`
- `PYPI_TOKEN`, `TEST_PYPI_TOKEN`, and `CODECOV_TOKEN` added to github secrets
- `.env` and other common evironment file name added to the `.gitignore` for token security.

### Changes
- Release workflow updated to have matching secrets name.

### Fixes
- Updated dependencies and improve type hints in codebase (ruff compliance).
- Update build tooling installation in release .
- Included pyproject.toml in sdist build targets.

## [0.1.0] - 2025-09-30
### Added
- Initial project scaffolding with Hatchling build system and CI/release workflows.
- Core chunking data models (`Document`, `Chunk`, `ChunkerConfig`).
- Sliding-window fallback chunker with metadata-rich outputs.
- `ChunkPipeline` orchestration, registry, and filesystem loader.
- Sphinx documentation skeleton and Read the Docs configuration.
- Pytest and Ruff tooling with baseline tests for the sliding-window chunker.
