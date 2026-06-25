from contract_review.config import load_settings
from contract_review.llm import FakeLLM
from contract_review.models import Document, Span, Verdict
from contract_review.pipeline import review
from contract_review.playbook.loader import load_named
from contract_review.stages.report import build_report
from contract_review.stages.verify import verify, check
from contract_review.models import Assessment, VerifiedAssessment, Rule, Playbook


def _doc():
    text = "No reverse engineering. Obligations survive termination."
    return Document(id="1", source_name="a.txt", text=text,
                    spans=[Span(id="s0", start=0, end=23, text=text[0:23]),
                           Span(id="s1", start=24, end=56, text=text[24:56])])


# ---- verify ----

def test_verify_flags_missing_and_nonexistent_evidence():
    doc = _doc()
    missing = Assessment(rule_id="r", verdict=Verdict.ENTAILMENT, evidence_span_ids=[])
    ghost = Assessment(rule_id="r", verdict=Verdict.ENTAILMENT, evidence_span_ids=["s99"])
    ok = Assessment(rule_id="r", verdict=Verdict.ENTAILMENT, evidence_span_ids=["s0"])
    assert not verify(missing, doc).checks_passed
    assert not verify(ghost, doc).checks_passed
    assert verify(ok, doc).checks_passed
    # NotMentioned needs no evidence
    assert verify(Assessment(rule_id="r", verdict=Verdict.NOT_MENTIONED), doc).checks_passed


# ---- report ----

def test_report_marks_deviations_and_scores():
    pb = Playbook(id="pb", name="PB", rules=(
        Rule(id="r1", name="A", statement="s", expected_disposition=Verdict.ENTAILMENT),
        Rule(id="r2", name="B", statement="s", expected_disposition=Verdict.NOT_MENTIONED),
    ))
    verified = [
        VerifiedAssessment(assessment=Assessment(rule_id="r1", verdict=Verdict.CONTRADICTION,
                                                 evidence_span_ids=["s0"]), checks_passed=True, attempts=1),
        VerifiedAssessment(assessment=Assessment(rule_id="r2", verdict=Verdict.NOT_MENTIONED),
                           checks_passed=True, attempts=1),
    ]
    report = build_report(pb, verified, document_id="1")
    assert report.deviation_score == 0.5
    devs = {f.rule_id for f in report.deviations}
    assert devs == {"r1"}
    assert report.findings[0].suggested_redline is not None
    assert report.findings[1].suggested_redline is None


# ---- end-to-end with FakeLLM ----

def test_pipeline_runs_end_to_end_with_fake_llm():
    doc = _doc()
    pb = load_named("nda_contractnli")

    # FakeLLM that "entails" the reverse-engineering rule and is silent otherwise.
    def responder(*, prompt, tool, tool_name):
        if "reverse engineer" in prompt.lower():
            return {"verdict": "Entailment", "evidence_span_ids": ["s0"], "rationale": "s0"}
        return {"verdict": "NotMentioned", "evidence_span_ids": [], "rationale": "silent"}

    report = review(doc, pb, FakeLLM(extract_fn=responder), settings=load_settings())
    assert report.document_id == "1"
    assert len(report.findings) == len(pb)
    # nda-11 expected Entailment and we entailed it -> not a deviation
    nda11 = next(f for f in report.findings if f.rule_id == "nda-11")
    assert nda11.actual is Verdict.ENTAILMENT and not nda11.is_deviation
    assert 0.0 <= report.deviation_score <= 1.0


# ---- concurrency ----

def test_pipeline_assesses_rules_concurrently():
    import threading
    import time

    doc = _doc()
    pb = load_named("nda_contractnli")
    lock = threading.Lock()
    state = {"active": 0, "max_active": 0}

    def responder(*, prompt, tool, tool_name):
        with lock:
            state["active"] += 1
            state["max_active"] = max(state["max_active"], state["active"])
        time.sleep(0.02)
        with lock:
            state["active"] -= 1
        return {"verdict": "NotMentioned", "evidence_span_ids": [], "rationale": "x"}

    settings = load_settings().model_copy(update={"assess_concurrency": 4})
    report = review(doc, pb, FakeLLM(extract_fn=responder), settings=settings)
    assert len(report.findings) == len(pb)
    assert state["max_active"] >= 2  # rules were assessed in parallel


def test_pipeline_preserves_rule_order_under_concurrency():
    doc = _doc()
    pb = load_named("nda_contractnli")
    settings = load_settings().model_copy(update={"assess_concurrency": 8})
    report = review(doc, pb, FakeLLM(), settings=settings)
    assert [f.rule_id for f in report.findings] == [r.id for r in pb.rules]


def test_pipeline_sequential_when_concurrency_is_one():
    doc = _doc()
    pb = load_named("nda_contractnli")
    settings = load_settings().model_copy(update={"assess_concurrency": 1})
    report = review(doc, pb, FakeLLM(), settings=settings)
    assert [f.rule_id for f in report.findings] == [r.id for r in pb.rules]
