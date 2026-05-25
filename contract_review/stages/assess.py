"""Stage 3 - Assess: judge a rule against its retrieved context.

Status: stub. This is the agentic core: a reasoning model reads the rule and the
ID-tagged candidate spans and returns a verdict, the cited evidence spans, and a
rationale. Implemented in a later step.
"""

from __future__ import annotations

from ..models import Assessment, RetrievedContext, Rule


def assess(rule: Rule, context: RetrievedContext) -> Assessment:
    raise NotImplementedError("assess: implemented in a later step")
