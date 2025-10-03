"""Built-in chunker implementations."""

from .fallback import SlidingWindowChunker
from .markdown import MarkdownHeadingChunker
from .python import PythonSemanticChunker
from .text import PlainTextChunker
from .yaml_json import JSONYamlChunker
from ..registry import DEFAULT_REGISTRY

_DEFAULT_FALLBACK = SlidingWindowChunker()
_PYTHON_CHUNKER = PythonSemanticChunker(_DEFAULT_FALLBACK)
_MARKDOWN_CHUNKER = MarkdownHeadingChunker(_DEFAULT_FALLBACK)
_STRUCTURED_CHUNKER = JSONYamlChunker(_DEFAULT_FALLBACK)
_TEXT_CHUNKER = PlainTextChunker(_DEFAULT_FALLBACK)

DEFAULT_REGISTRY.register(["py", "pyi", "pyx"], _PYTHON_CHUNKER)
DEFAULT_REGISTRY.register(["md", "markdown", "mdx"], _MARKDOWN_CHUNKER)
DEFAULT_REGISTRY.register(["json"], _STRUCTURED_CHUNKER)
DEFAULT_REGISTRY.register(["yaml", "yml"], _STRUCTURED_CHUNKER)
DEFAULT_REGISTRY.register(["txt", "text", "log"], _TEXT_CHUNKER)

__all__ = [
    "SlidingWindowChunker",
    "MarkdownHeadingChunker",
    "PythonSemanticChunker",
    "PlainTextChunker",
    "JSONYamlChunker",
]
