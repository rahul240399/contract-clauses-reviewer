"""Metrics comparing predicted Assessments to gold annotations.

Two families, matching what actually matters for this task:
- Verdict quality: accuracy plus macro-F1 (macro because NotMentioned dominates,
  so plain accuracy flatters a lazy classifier).
- Evidence quality: micro precision/recall/F1 over the cited span ids, computed
  only where gold has evidence (Entailment/Contradiction).
"""

from __future__ import annotations

from pydantic import BaseModel

from contract_review.models import Assessment, Verdict

from .oracle import GoldAnnotation

Pair = tuple[Assessment, GoldAnnotation]


class EvalResult(BaseModel):
    n: int
    verdict_accuracy: float
    verdict_macro_f1: float
    evidence_precision: float
    evidence_recall: float
    evidence_f1: float


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def verdict_accuracy(pairs: list[Pair]) -> float:
    if not pairs:
        return 0.0
    correct = sum(1 for pred, gold in pairs if pred.verdict == gold.verdict)
    return correct / len(pairs)


def verdict_macro_f1(pairs: list[Pair]) -> float:
    f1s: list[float] = []
    for cls in Verdict:
        tp = sum(1 for p, g in pairs if p.verdict == cls and g.verdict == cls)
        fp = sum(1 for p, g in pairs if p.verdict == cls and g.verdict != cls)
        fn = sum(1 for p, g in pairs if p.verdict != cls and g.verdict == cls)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1s.append(_safe_div(2 * precision * recall, precision + recall))
    return _safe_div(sum(f1s), len(f1s))


def evidence_prf(pairs: list[Pair]) -> tuple[float, float, float]:
    tp = fp = fn = 0
    for pred, gold in pairs:
        if not gold.evidence_span_ids:
            continue  # NotMentioned: no evidence to score
        pred_set = set(pred.evidence_span_ids)
        gold_set = set(gold.evidence_span_ids)
        tp += len(pred_set & gold_set)
        fp += len(pred_set - gold_set)
        fn += len(gold_set - pred_set)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return precision, recall, f1


def evaluate(pairs: list[Pair]) -> EvalResult:
    precision, recall, f1 = evidence_prf(pairs)
    return EvalResult(
        n=len(pairs),
        verdict_accuracy=verdict_accuracy(pairs),
        verdict_macro_f1=verdict_macro_f1(pairs),
        evidence_precision=precision,
        evidence_recall=recall,
        evidence_f1=f1,
    )
