# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Updated release workflow to pin the latest PyPI publish action and add a `twine check`, resolving bogus 'Missing Name/Version' errors during automated releases.

## [0.2.1] - TBD

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
