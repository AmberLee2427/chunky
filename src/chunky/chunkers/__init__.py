"""Built-in chunker implementations."""

from ..registry import DEFAULT_REGISTRY
from .fallback import SlidingWindowChunker
from .fortran import FortranChunker
from .markdown import MarkdownHeadingChunker
from .python import PythonSemanticChunker
from .text import PlainTextChunker
from .yaml_json import JSONYamlChunker

try:  # Optional Tree-sitter support
    from .treesitter import TreeSitterChunker, TreeSitterSpec
except Exception:  # pragma: no cover - optional dependency not installed
    TreeSitterChunker = None  # type: ignore
    TreeSitterSpec = None  # type: ignore

_DEFAULT_FALLBACK = SlidingWindowChunker()
_PYTHON_CHUNKER = PythonSemanticChunker(_DEFAULT_FALLBACK)
_MARKDOWN_CHUNKER = MarkdownHeadingChunker(_DEFAULT_FALLBACK)
_STRUCTURED_CHUNKER = JSONYamlChunker(_DEFAULT_FALLBACK)
_TEXT_CHUNKER = PlainTextChunker(_DEFAULT_FALLBACK)
_FORTRAN_CHUNKER = FortranChunker(_DEFAULT_FALLBACK)

DEFAULT_REGISTRY.register(["py", "pyi", "pyx"], _PYTHON_CHUNKER)
DEFAULT_REGISTRY.register(["md", "markdown", "mdx"], _MARKDOWN_CHUNKER)
DEFAULT_REGISTRY.register(["json"], _STRUCTURED_CHUNKER)
DEFAULT_REGISTRY.register(["yaml", "yml"], _STRUCTURED_CHUNKER)
DEFAULT_REGISTRY.register(["txt", "text", "log"], _TEXT_CHUNKER)
DEFAULT_REGISTRY.register(["f", "f90", "f95", "f03", "for"], _FORTRAN_CHUNKER)

if TreeSitterChunker and TreeSitterSpec:
    ts_specs = [
        (
            TreeSitterSpec(
                language="c",
                query="(function_definition) @chunk",
                metadata={"chunk_type": "c"},
            ),
            ["c", "h"],
        ),
        (
            TreeSitterSpec(
                language="cpp",
                query="(function_definition) @chunk",
                metadata={"chunk_type": "cpp"},
            ),
            ["cc", "cpp", "cxx", "hh", "hpp", "hxx", "ino"],
        ),
        (
            TreeSitterSpec(
                language="html",
                query="""
                (
                  (element
                    (start_tag (tag_name) @tag)
                  ) @chunk
                  (#match? @tag "section|article|div|main")
                )
                """,
                metadata={"chunk_type": "html"},
            ),
            ["html", "htm", "xhtml"],
        ),
        (
            TreeSitterSpec(
                language="bash",
                query="(function_definition) @chunk",
                metadata={"chunk_type": "bash"},
            ),
            ["sh", "bash", "zsh"],
        ),
    ]

    for spec, extensions in ts_specs:
        try:
            chunker = TreeSitterChunker(spec, _DEFAULT_FALLBACK)
        except Exception:  # pragma: no cover - guard against runtime issues
            continue
        DEFAULT_REGISTRY.register(extensions, chunker, overwrite=True)

__all__ = [
    "SlidingWindowChunker",
    "MarkdownHeadingChunker",
    "PythonSemanticChunker",
    "PlainTextChunker",
    "JSONYamlChunker",
    "FortranChunker",
]
