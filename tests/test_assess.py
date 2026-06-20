import pytest

from contract_review.llm import FakeLLM
from contract_review.models import Document, RetrievedContext, Rule, Span, Verdict
from contract_review.stages.assess import assess
from contract_review.stages.match import match


def _doc():
    text = "No reverse engineering. Obligations survive termination."
    return Document(
        id="1",
        source_name="a.txt",
        text=text,
        spans=[Span(id="s0", start=0, end=23, text=text[0:23]),
               Span(id="s1", start=24, end=56, text=text[24:56])],
    )


def _rule():
    return Rule(id="nda-11", name="No reverse engineering",
                statement="Receiving Party shall not reverse engineer.",
                expected_disposition=Verdict.ENTAILMENT)


def test_assess_runs_two_steps_and_returns_grounded_verdict():
    doc, rule = _doc(), _rule()
    ctx = match(doc, rule)
    llm = FakeLLM(default_extract={"verdict": "Entailment",
                                   "evidence_span_ids": ["s0"],
                                   "rationale": "clause s0 forbids it"})
    result = assess(rule, ctx, llm)
    assert result.verdict is Verdict.ENTAILMENT
    assert result.evidence_span_ids == ["s0"]
    # two-step: think then extract, in order
    assert [c[0] for c in llm.calls] == ["think", "extract"]


def test_not_mentioned_strips_evidence():
    doc, rule = _doc(), _rule()
    ctx = match(doc, rule)
    llm = FakeLLM(default_extract={"verdict": "NotMentioned",
                                   "evidence_span_ids": ["s0"],  # should be dropped
                                   "rationale": "silent"})
    result = assess(rule, ctx, llm)
    assert result.verdict is Verdict.NOT_MENTIONED
    assert result.evidence_span_ids == []


def test_invalid_verdict_raises():
    doc, rule = _doc(), _rule()
    ctx = match(doc, rule)
    llm = FakeLLM(default_extract={"verdict": "Maybe", "evidence_span_ids": [], "rationale": ""})
    with pytest.raises(ValueError, match="invalid verdict"):
        assess(rule, ctx, llm)
