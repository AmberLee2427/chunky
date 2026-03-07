# TODOs

## 2. Improve tree-sitter query coverage (Option B)
- [ ] Extend the C/C++ tree-sitter query to explicitly capture top-level non-function nodes:
  `class_specifier`, `struct_specifier`, `declaration`, `preproc_include`,
  `namespace_definition`, `comment`
- [ ] Do the same for the Bash and HTML specs
- [ ] Add per-language metadata tags so callers can distinguish semantic node types
  (e.g. `chunk_type: "cpp_class"` vs `"cpp_function"` vs `"cpp_context"`)
- [ ] Gap-filling (Option A, see `TREESITTER_COVERAGE_BUG.md`) must land first
- [ ] Update tests in `tests/test_language_chunkers.py` accordingly

## 1. Get 'chunky' name on PyPI
- [ ] Investigate if the 'chunky' project on PyPI is abandoned
- [ ] If abandoned, follow PyPI's process for requesting a name transfer: [PyPI Name Claim Help](https://pypi.org/help/#claiming-a-name)
- [ ] If successful, update `pyproject.toml` and republish as `chunky`
