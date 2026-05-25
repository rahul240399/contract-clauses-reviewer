"""End-to-end orchestration of the review workflow.

Status: stub. Wires the stages together and runs the verify -> assess retry loop:

    segment -> for each rule: match -> assess -> verify (retry) -> report

Implemented once the individual stages land.
"""

from __future__ import annotations

from .models import Document, Playbook, Report


def review(document: Document, playbook: Playbook) -> Report:
    raise NotImplementedError("pipeline.review: wired in a later step")
