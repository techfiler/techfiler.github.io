"""Sentence selection for the quick-learning edition.

The highlighted edition marks the load-bearing sentence of each passage in
yellow so the book can be skimmed. Selection is shared by both renderers:
`pick` returns character spans, the PDF builder turns them into markup and the
DOCX builder turns them into runs, so the two editions always agree on what is
highlighted.

The rule follows how the content is written. An answer leads with its claim, so
the highlight goes at the front. A production-context paragraph builds to its
consequence, so the highlight goes at the end.
"""

from __future__ import annotations

import re
from typing import List, Tuple

Span = Tuple[int, int]

# Split after . ! or ? when whitespace and a new sentence follow. Decimals,
# version numbers and abbreviations have no space after the dot, so they are
# never treated as sentence ends.
_BREAK = re.compile(r'(?<=[.!?])\s+(?=["\u201c(]?[A-Z0-9])')

# A lead sentence shorter than this is a fragment on its own, so the next
# sentence is pulled in when the caller allows more than one.
_SHORT_LEAD = 110

# A trailing sentence shorter than this carries no meaning without the one
# before it, so it is extended backwards even at limit 1.
_SHORT_TAIL = 60

# Beyond this a highlight stops being a highlight and becomes a yellow block.
_MAX_SPAN = 520


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sentence_spans(text: str) -> List[Span]:
    """Character spans of each sentence, ignoring surrounding whitespace."""
    body = text.strip()
    offset = text.find(body) if body else 0
    spans: List[Span] = []
    start = 0
    for match in _BREAK.finditer(body):
        spans.append((offset + start, offset + match.start()))
        start = match.end()
    if start < len(body):
        spans.append((offset + start, offset + len(body)))
    return spans


def pick(text: str, lead: bool = False, limit: int = 1) -> List[Span]:
    """Choose the span(s) worth highlighting in this passage."""
    if limit <= 0 or not text.strip():
        return []
    sentences = sentence_spans(text)
    if not sentences:
        return []

    if lead:
        start, end = sentences[0]
        taken = 1
        while taken < limit and taken < len(sentences) and (end - start) < _SHORT_LEAD:
            extended = sentences[taken][1]
            if extended - start > _MAX_SPAN:
                break
            end = extended
            taken += 1
    else:
        index = len(sentences) - 1
        start, end = sentences[index]
        while (end - start) < _SHORT_TAIL and index > 0:
            index -= 1
            if end - sentences[index][0] > _MAX_SPAN:
                break
            start = sentences[index][0]

    if end - start > _MAX_SPAN:
        return []
    return [(start, end)]


def markup(text: str, spans: List[Span], open_tag: str, close_tag: str) -> str:
    """Escape the text and wrap the chosen spans in the given tags."""
    out: List[str] = []
    cursor = 0
    for start, end in spans:
        if start > cursor:
            out.append(escape(text[cursor:start]))
        out.append(f"{open_tag}{escape(text[start:end])}{close_tag}")
        cursor = end
    out.append(escape(text[cursor:]))
    return "".join(out)
