"""End-to-end orchestration of the review workflow.

    for rule in playbook:
        match -> assess -> verify ; re-assess while checks fail (retry budget)
    build_report(...)

Runs against any LLM-port implementation (FakeLLM for tests, OpenAICompatibleLLM
for real models). Rules are independent, so they are assessed concurrently with a
bounded thread pool (the per-rule work is I/O-bound model calls). The bound comes
from settings.assess_concurrency; set it to 1 for fully sequential execution.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .config import Settings, load_settings
from .models import (
    Assessment,
    Document,
    Playbook,
    Report,
    Rule,
    VerifiedAssessment,
    Verdict,
)
from .ports import LLM
from .stages.assess import assess
from .stages.match import match
from .stages.report import build_report
from .stages.verify import verify


def review(
    document: Document,
    playbook: Playbook,
    llm: LLM,
    *,
    settings: Settings | None = None,
) -> Report:
    settings = settings or load_settings()
    rules = playbook.rules
    workers = max(1, min(settings.assess_concurrency, len(rules) or 1))
    if workers == 1:
        verified = [_assess_with_retries(r, document, llm, settings) for r in rules]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # map preserves input order, so findings stay aligned with the playbook.
            verified = list(
                pool.map(lambda r: _assess_with_retries(r, document, llm, settings), rules)
            )
    return build_report(playbook, verified, document_id=document.id)


def _assess_with_retries(
    rule: Rule, document: Document, llm: LLM, settings: Settings
) -> VerifiedAssessment:
    context = match(document, rule)
    last: VerifiedAssessment | None = None
    for attempt in range(1, settings.max_assess_attempts + 1):
        try:
            assessment = assess(
                rule, context, llm, max_reasoning_tokens=settings.max_reasoning_tokens
            )
        except ValueError as exc:
            last = VerifiedAssessment(
                assessment=Assessment(
                    rule_id=rule.id, verdict=Verdict.NOT_MENTIONED,
                    evidence_span_ids=[], rationale=f"assess error: {exc}",
                ),
                checks_passed=False,
                attempts=attempt,
                notes=str(exc),
            )
            continue
        candidate = verify(assessment, document, attempts=attempt)
        if candidate.checks_passed:
            return candidate
        last = candidate
    assert last is not None
    return last
