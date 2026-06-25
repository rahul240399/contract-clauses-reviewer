"""ContractNLI gold annotations: the objective evaluation oracle.

Loads the per-(document, rule) gold verdict and evidence spans. This is an answer
key for measuring the assess stage, not training data. Evidence indices are mapped
to the same span ids the pipeline uses ("s{index}") so predictions and gold are
directly comparable.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from contract_review.datasets.contractnli import load_raw_split
from contract_review.models import Verdict


class GoldAnnotation(BaseModel):
    rule_id: str
    verdict: Verdict
    evidence_span_ids: list[str] = Field(default_factory=list)


def gold_for_document(raw_doc: dict) -> dict[str, GoldAnnotation]:
    """Return {rule_id: GoldAnnotation} for one ContractNLI document record."""
    annotations = raw_doc["annotation_sets"][0]["annotations"]
    result: dict[str, GoldAnnotation] = {}
    for rule_id, annotation in annotations.items():
        result[rule_id] = GoldAnnotation(
            rule_id=rule_id,
            verdict=Verdict(annotation["choice"]),
            evidence_span_ids=[f"s{i}" for i in annotation.get("spans", [])],
        )
    return result


def load_gold(
    split: str, data_dir: str | Path | None = None
) -> dict[str, dict[str, GoldAnnotation]]:
    """Return {document_id: {rule_id: GoldAnnotation}} for a split."""
    raw = load_raw_split(split, data_dir)
    return {str(doc["id"]): gold_for_document(doc) for doc in raw["documents"]}
