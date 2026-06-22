"""Stage 1 - Segment: turn raw contract text into a segmented Document.

A simple, dependency-free segmenter for uploaded plain-text contracts: split on
line breaks and sentence-final punctuation, keeping exact character offsets so
downstream evidence can be resolved back to the source. For ContractNLI we use
the dataset's gold spans instead (see datasets/contractnli.py); a richer
PDF-aware segmenter can replace this without touching other stages.
"""

from __future__ import annotations

from ..models import Document, Span

_SENTENCE_END = ".;!?"


def _raw_segments(text: str) -> list[tuple[int, int]]:
    """Yield (start, end) cuts on newlines and sentence-final punctuation."""
    cuts: list[tuple[int, int]] = []
    start = 0
    n = len(text)
    for i, ch in enumerate(text):
        is_newline = ch == "\n"
        is_sentence_end = ch in _SENTENCE_END and (i + 1 >= n or text[i + 1].isspace())
        if is_newline or is_sentence_end:
            end = i if is_newline else i + 1
            cuts.append((start, end))
            start = i + 1
    if start < n:
        cuts.append((start, n))
    return cuts


def segment(text: str, *, source_name: str, doc_id: str) -> Document:
    spans: list[Span] = []
    index = 0
    for start, end in _raw_segments(text):
        chunk = text[start:end]
        lead = len(chunk) - len(chunk.lstrip())
        trail = len(chunk) - len(chunk.rstrip())
        s, e = start + lead, end - trail
        if e <= s:
            continue  # whitespace-only segment
        spans.append(Span(id=f"s{index}", start=s, end=e, text=text[s:e]))
        index += 1
    return Document(id=doc_id, source_name=source_name, text=text, spans=spans)
