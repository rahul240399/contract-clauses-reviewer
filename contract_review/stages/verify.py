"""Stage 4 - Verify & reflect: validate a verdict and retry on failure.

Status: stub. Runs cheap code-based checks first (every Entailment/Contradiction
must cite a span; cited span text must exist in the document) and an optional
self-critique. On failure the assessment is bounced back to assess, up to a
retry budget. Implemented in a later step.
"""

from __future__ import annotations

from ..models import Assessment, Document, VerifiedAssessment


def verify(assessment: Assessment, document: Document) -> VerifiedAssessment:
    raise NotImplementedError("verify: implemented in a later step")
