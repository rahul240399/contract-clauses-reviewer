"""Stage 5 - Report: compare verdicts to playbook stance; draft redlines + score.

Status: stub. Deterministic stage. For each rule it compares the actual verdict
to the rule's expected disposition, marks deviations, drafts a suggested redline
for each deviation, and computes the deviation score. Implemented in a later step.
"""

from __future__ import annotations

from ..models import Playbook, Report, VerifiedAssessment


def build_report(
    playbook: Playbook,
    verified: list[VerifiedAssessment],
    *,
    document_id: str,
) -> Report:
    raise NotImplementedError("report: implemented in a later step")
