"""Stage 1 - Segment: raw contract text/PDF into a segmented Document.

Status: stub. Deterministic stage; implemented in a later step. During early
development the segmentation is taken from ContractNLI's gold spans, with a real
text/PDF segmenter added before contract upload is supported.
"""

from __future__ import annotations

from ..models import Document


def segment(text: str, *, source_name: str, doc_id: str) -> Document:
    raise NotImplementedError("segment: implemented in a later step")
