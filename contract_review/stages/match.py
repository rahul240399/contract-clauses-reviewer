"""Stage 2 - Match: locate where each playbook rule is relevant in the document.

Status: stub. Deterministic stage. The v1 default returns the whole document as
context (long-context assessment); a retrieve-with-window strategy can replace
this behind the same RetrievedContext interface.
"""

from __future__ import annotations

from ..models import Document, RetrievedContext, Rule


def match(document: Document, rule: Rule) -> RetrievedContext:
    raise NotImplementedError("match: implemented in a later step")
