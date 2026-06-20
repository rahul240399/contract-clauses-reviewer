"""Stage 3 - Assess: judge a rule against its retrieved context (the agentic core).

Two steps over the LLM port:
1. think()   - free-form reasoning over the rule and ID-tagged clauses.
2. extract() - a forced submit_assessment tool call turning that reasoning into a
   structured {verdict, evidence_span_ids, rationale}.

Evidence is cited by clause id so grounding can be verified downstream.
"""

from __future__ import annotations

from ..models import Assessment, RetrievedContext, Rule, Verdict
from ..ports import LLM
from ..prompts import (
    ASSESS_SYSTEM,
    ASSESS_TOOL,
    ASSESS_TOOL_NAME,
    build_extract_prompt,
    build_think_prompt,
)


def assess(
    rule: Rule,
    context: RetrievedContext,
    llm: LLM,
    *,
    max_reasoning_tokens: int = 1024,
) -> Assessment:
    reasoning = llm.think(
        system=ASSESS_SYSTEM,
        prompt=build_think_prompt(rule, context),
        max_thinking_tokens=max_reasoning_tokens,
    )
    raw = llm.extract(
        system=ASSESS_SYSTEM,
        prompt=build_extract_prompt(rule, context, reasoning),
        tool=ASSESS_TOOL,
        tool_name=ASSESS_TOOL_NAME,
    )
    return _to_assessment(rule.id, raw)


def _to_assessment(rule_id: str, raw: dict) -> Assessment:
    raw_verdict = str(raw.get("verdict", "")).strip()
    try:
        verdict = Verdict(raw_verdict)
    except ValueError:
        raise ValueError(f"assess: model returned invalid verdict {raw_verdict!r}")

    spans = raw.get("evidence_span_ids") or []
    if not isinstance(spans, list):
        spans = [spans]
    spans = [str(s).strip() for s in spans if str(s).strip()]

    # NotMentioned never carries evidence.
    if verdict is Verdict.NOT_MENTIONED:
        spans = []

    return Assessment(
        rule_id=rule_id,
        verdict=verdict,
        evidence_span_ids=spans,
        rationale=str(raw.get("rationale", "")).strip(),
    )
