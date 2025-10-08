# Requested Enhancements for `chunky`

Here’s what Nancy Brain needs from chunky so the KB build can index documents the way it used to:

## 1. Stable Chunk IDs

- The KB build expects chunk identifiers in the form <doc_id>#chunk-0000.
- Let callers supply a logical document ID (e.g., category/repo/relative/path.py) via Document.metadata["doc_id"] or similar.
- Every emitted chunk should use that logical ID to build its chunk ID:
`"{doc_id}#chunk-{index:04d}"`.

## 2. Metadata Normalisation

Each chunk should carry the following fields (JSON-serialisable), matching the old SmartChunker output:

| Field | Type | Notes |
| :-: | :-: | :-: |
| chunk_index | int | 0-based |
| chunk_count | int | total chunks produced for the logical document |
| source_document | str | logical doc ID (category/repo/...) |
| line_start | int | 1-based inclusive |
| line_end | int | inclusive |
| span_start | int | 0-based char offset |
| span_end | int | 0-based char offset |

If the caller wants to add extra metadata (e.g., `relative_path`, `repository`, etc.) it should remain mergeable with these fields.

## 3. Configurability

- Allow the logical document ID key (e.g., "doc_id") and chunk ID format to be customised via ChunkerConfig so other projects can choose a different suffix.
- Default to the Nancy Brain-compatible values above.
