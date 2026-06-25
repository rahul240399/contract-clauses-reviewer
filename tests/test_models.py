import pytest
from pydantic import ValidationError

from contract_review.models import (
    Document,
    Finding,
    Playbook,
    Report,
    Rule,
    Span,
    Verdict,
)


def test_span_rejects_inverted_offsets():
    with pytest.raises(ValidationError):
        Span(id="x", start=5, end=2, text="z")


def test_span_rejects_negative_start():
    with pytest.raises(ValidationError):
        Span(id="x", start=-1, end=2, text="z")


def test_document_span_lookup():
    doc = Document(
        id="1",
        source_name="a.txt",
        text="AB CD",
        spans=[Span(id="s0", start=0, end=2, text="AB"), Span(id="s1", start=3, end=5, text="CD")],
    )
    assert doc.span_by_id("s1").text == "CD"
    assert doc.span_by_id("missing") is None


def test_playbook_is_frozen_and_indexable():
    pb = Playbook(
        id="pb",
        name="PB",
        rules=(Rule(id="r1", name="n", statement="s", expected_disposition=Verdict.ENTAILMENT),),
    )
    assert len(pb) == 1
    assert pb.rule_by_id("r1").expected_disposition is Verdict.ENTAILMENT
    with pytest.raises(ValidationError):
        pb.id = "other"


def test_report_json_round_trip_and_deviations():
    report = Report(
        document_id="1",
        playbook_id="pb",
        findings=[
            Finding(rule_id="r1", rule_name="n", expected=Verdict.ENTAILMENT,
                    actual=Verdict.CONTRADICTION, is_deviation=True, evidence_span_ids=["s0"]),
            Finding(rule_id="r2", rule_name="m", expected=Verdict.ENTAILMENT,
                    actual=Verdict.ENTAILMENT, is_deviation=False),
        ],
        deviation_score=0.5,
    )
    restored = Report.model_validate_json(report.model_dump_json())
    assert restored.deviation_score == 0.5
    assert [f.rule_id for f in restored.deviations] == ["r1"]
