"""Stage 2 - Match: build the context the assess stage reasons over.

For each rule we produce a RetrievedContext: the candidate spans plus a text block
to put in front of the model. The block is the document rendered as ID-tagged
spans ("[s0] ...\\n[s1] ...") so the assess stage can cite evidence by span id and
we can resolve those ids back to authoritative offsets in the Document.

v1 strategy is long-context: the whole document is the context for every rule, so
nothing can be missed by a retrieval step. The per-rule signature is kept so a
retrieve-with-window strategy can replace the body later without touching assess.
"""

from __future__ import annotations

from ..models import Document, RetrievedContext, Rule


def render_spans(document: Document, span_ids: list[str]) -> str:
    """Render the given spans as an ID-tagged block for the model to read and cite.

    Internal whitespace is collapsed for prompt cleanliness; this only affects the
    text shown to the model. The authoritative text and offsets stay on the Span.
    """
    lines: list[str] = []
    for span_id in span_ids:
        span = document.span_by_id(span_id)
        if span is None:
            continue
        normalized = " ".join(span.text.split())
        lines.append(f"[{span.id}] {normalized}")
    return "\n".join(lines)


def match(document: Document, rule: Rule) -> RetrievedContext:
    # v1 long-context: every span is a candidate; the rule does not narrow the
    # context yet. A future retrieval strategy would select a subset here.
    span_ids = [span.id for span in document.spans]
    return RetrievedContext(
        rule_id=rule.id,
        candidate_span_ids=span_ids,
        context_text=render_spans(document, span_ids),
    )
