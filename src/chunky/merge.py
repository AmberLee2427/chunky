"""Forward-merge utility for small chunks."""

from __future__ import annotations

import dataclasses

from .types import Chunk


def merge_small_chunks(chunks: list[Chunk], min_chars: int) -> list[Chunk]:
    """Merge chunks smaller than ``min_chars`` into their successor."""

    if min_chars <= 0 or not chunks:
        return chunks

    result: list[Chunk] = []
    carry: list[str] = []
    changed = False

    for chunk in chunks:
        if len(chunk.text.strip()) < min_chars:
            carry.append(chunk.text)
            changed = True
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
            result[-1] = dataclasses.replace(last, text=last.text + "\n" + "\n".join(carry))
        else:
            # Edge case: every chunk was tiny; emit each one so content is never dropped.
            return chunks

    if not changed:
        return chunks
    return result


__all__ = ["merge_small_chunks"]
