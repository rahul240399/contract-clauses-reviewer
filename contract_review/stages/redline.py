"""Stage 5b - Redline: draft model-written amendments for deviating findings.

The report stage marks deviations and attaches a deterministic, templated
redline. This stage enriches each deviation with an LLM-drafted redline: concrete
proposed clause language grounded in the deviating clause(s). It is best-effort -
any failure (network error, no tool call, empty text) leaves the templated
fallback in place, so the report is always complete even offline.

Deviations are independent, so they are drafted concurrently with a bounded
thread pool, mirroring the assess stage.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from ..models import Document, Finding, Playbook, Report, Rule
from ..ports import LLM
from ..prompts import REDLINE_SYSTEM, REDLINE_TOOL, REDLINE_TOOL_NAME, build_redline_prompt


def _evidence_text(finding: Finding, document: Document) -> str:
    spans = (document.span_by_id(sid) for sid in finding.evidence_span_ids)
    return "\n".join(f"[{s.id}] {s.text}" for s in spans if s is not None)


def draft_redline(rule: Rule, finding: Finding, document: Document, llm: LLM) -> str | None:
    """Draft one redline, or return None to fall back to the templated wording."""
    prompt = build_redline_prompt(rule, finding, _evidence_text(finding, document))
    try:
        raw = llm.extract(
            system=REDLINE_SYSTEM,
            prompt=prompt,
            tool=REDLINE_TOOL,
            tool_name=REDLINE_TOOL_NAME,
        )
    except Exception:
        return None
    text = str(raw.get("redline", "")).strip()
    return text or None


def draft_redlines(
    report: Report,
    playbook: Playbook,
    document: Document,
    llm: LLM,
    *,
    concurrency: int = 4,
) -> Report:
    """Return a copy of the report with model-drafted redlines on its deviations."""
    targets = [i for i, f in enumerate(report.findings) if f.is_deviation]
    if not targets:
        return report

    def work(index: int) -> tuple[int, str | None]:
        finding = report.findings[index]
        rule = playbook.rule_by_id(finding.rule_id)
        if rule is None:
            return index, None
        return index, draft_redline(rule, finding, document, llm)

    workers = max(1, min(concurrency, len(targets)))
    if workers == 1:
        results = [work(i) for i in targets]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(work, targets))

    findings = list(report.findings)
    for index, text in results:
        if text:
            findings[index] = findings[index].model_copy(update={"suggested_redline": text})
    return report.model_copy(update={"findings": findings})
