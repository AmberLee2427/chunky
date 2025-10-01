# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-09-30
### Added
- Initial project scaffolding with Hatchling build system and CI/release workflows.
- Core chunking data models (`Document`, `Chunk`, `ChunkerConfig`).
- Sliding-window fallback chunker with metadata-rich outputs.
- `ChunkPipeline` orchestration, registry, and filesystem loader.
- Sphinx documentation skeleton and Read the Docs configuration.
- Pytest and Ruff tooling with baseline tests for the sliding-window chunker.
