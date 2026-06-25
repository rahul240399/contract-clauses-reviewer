"""Stage 5 - Report: compare verdicts to playbook stance; draft redlines + score.

Deterministic. For each rule it compares the actual verdict to the rule's
expected disposition, marks deviations, attaches a templated suggested redline
for each deviation, and computes the deviation score (fraction of rules that
deviate). The templated redline is a fallback; the redline stage replaces it
with model-drafted wording when an LLM is available.
"""

from __future__ import annotations

from ..models import Finding, Playbook, Report, VerifiedAssessment, Verdict


def _fallback_redline(rule_name: str, expected: Verdict, actual: Verdict, span_ids: list[str]) -> str:
    where = f" (see clause(s) {', '.join(span_ids)})" if span_ids else ""
    return (
        f"'{rule_name}': contract is {actual.value} but the playbook expects "
        f"{expected.value}{where}. Amend the contract to align with the expected "
        f"position."
    )


def build_report(
    playbook: Playbook,
    verified: list[VerifiedAssessment],
    *,
    document_id: str,
) -> Report:
    by_rule = {va.assessment.rule_id: va for va in verified}

    findings: list[Finding] = []
    for rule in playbook.rules:
        va = by_rule.get(rule.id)
        if va is None:
            actual, evidence, rationale = Verdict.NOT_MENTIONED, [], "(not assessed)"
        else:
            actual = va.assessment.verdict
            evidence = va.assessment.evidence_span_ids
            rationale = va.assessment.rationale

        is_deviation = actual != rule.expected_disposition
        findings.append(
            Finding(
                rule_id=rule.id,
                rule_name=rule.name,
                expected=rule.expected_disposition,
                actual=actual,
                is_deviation=is_deviation,
                evidence_span_ids=evidence,
                rationale=rationale,
                suggested_redline=(
                    _fallback_redline(rule.name, rule.expected_disposition, actual, evidence)
                    if is_deviation
                    else None
                ),
            )
        )

    n_dev = sum(1 for f in findings if f.is_deviation)
    score = n_dev / len(findings) if findings else 0.0
    return Report(
        document_id=document_id,
        playbook_id=playbook.id,
        findings=findings,
        deviation_score=score,
        summary=f"{n_dev} of {len(findings)} rules deviate from the playbook.",
    )
