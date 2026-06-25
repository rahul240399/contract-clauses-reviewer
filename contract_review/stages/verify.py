"""Stage 4 - Verify: validate a verdict's grounding (cheap, code-based).

Two checks that catch the common failure modes before a human sees the result:
1. An Entailment/Contradiction must cite at least one evidence span.
2. Every cited span id must actually exist in the document.

verify reports pass/fail and notes; the re-assess-on-failure loop lives in the
pipeline (it owns the retry budget). An LLM self-critique can be added later.
"""

from __future__ import annotations

from ..models import Assessment, Document, VerifiedAssessment, Verdict


def check(assessment: Assessment, document: Document) -> list[str]:
    """Return a list of grounding problems (empty means the verdict is well-formed)."""
    problems: list[str] = []
    if assessment.verdict in (Verdict.ENTAILMENT, Verdict.CONTRADICTION):
        if not assessment.evidence_span_ids:
            problems.append(f"{assessment.verdict.value} requires evidence but none was cited")
        for span_id in assessment.evidence_span_ids:
            if document.span_by_id(span_id) is None:
                problems.append(f"cited span {span_id!r} does not exist in the document")
    return problems


def verify(
    assessment: Assessment, document: Document, *, attempts: int = 1
) -> VerifiedAssessment:
    problems = check(assessment, document)
    return VerifiedAssessment(
        assessment=assessment,
        checks_passed=not problems,
        attempts=attempts,
        notes="; ".join(problems),
    )
