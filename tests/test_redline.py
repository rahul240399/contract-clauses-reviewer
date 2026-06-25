from contract_review.config import load_settings
from contract_review.llm import ScriptedLLM
from contract_review.models import Document, Finding, Rule, Span, Verdict
from contract_review.pipeline import review
from contract_review.playbook.loader import load_named
from contract_review.stages.redline import draft_redline


def _doc():
    text = "No reverse engineering. Obligations survive termination."
    return Document(id="1", source_name="a.txt", text=text,
                    spans=[Span(id="s0", start=0, end=23, text=text[0:23]),
                           Span(id="s1", start=24, end=56, text=text[24:56])])


def _finding():
    return Finding(rule_id="nda-11", rule_name="No reverse engineering",
                   expected=Verdict.ENTAILMENT, actual=Verdict.NOT_MENTIONED,
                   is_deviation=True, evidence_span_ids=["s0"], rationale="silent")


def _rule():
    return Rule(id="nda-11", name="No reverse engineering",
                statement="Receiving Party shall not reverse engineer.",
                expected_disposition=Verdict.ENTAILMENT)


# ---- unit: draft_redline ----

def test_draft_redline_returns_model_text():
    llm = ScriptedLLM(extract_fn=lambda **_: {"redline": "Add: no reverse engineering."})
    assert draft_redline(_rule(), _finding(), _doc(), llm) == "Add: no reverse engineering."


def test_draft_redline_falls_back_when_empty():
    llm = ScriptedLLM(extract_fn=lambda **_: {"redline": "   "})
    assert draft_redline(_rule(), _finding(), _doc(), llm) is None


def test_draft_redline_falls_back_on_error():
    def boom(**_):
        raise ValueError("no tool call")

    assert draft_redline(_rule(), _finding(), _doc(), ScriptedLLM(extract_fn=boom)) is None


# ---- pipeline integration ----

def _responder(*, prompt, tool, tool_name):
    if tool_name == "submit_redline":
        return {"redline": "MODEL REDLINE"}
    return {"verdict": "NotMentioned", "evidence_span_ids": [], "rationale": "x"}


def test_pipeline_uses_model_redlines_for_deviations():
    report = review(_doc(), load_named("nda_contractnli"),
                    ScriptedLLM(extract_fn=_responder), settings=load_settings())
    deviations = [f for f in report.findings if f.is_deviation]
    assert deviations
    assert all(f.suggested_redline == "MODEL REDLINE" for f in deviations)
    # non-deviations carry no redline
    assert all(f.suggested_redline is None for f in report.findings if not f.is_deviation)


def test_pipeline_falls_back_to_template_without_model_redline():
    # default ScriptedLLM returns no "redline" key -> templated fallback stays.
    report = review(_doc(), load_named("nda_contractnli"),
                    ScriptedLLM(), settings=load_settings())
    deviations = [f for f in report.findings if f.is_deviation]
    assert deviations
    assert all("Amend the contract" in f.suggested_redline for f in deviations)


def test_with_redlines_false_skips_model_drafting():
    report = review(_doc(), load_named("nda_contractnli"),
                    ScriptedLLM(extract_fn=_responder), settings=load_settings(),
                    with_redlines=False)
    deviations = [f for f in report.findings if f.is_deviation]
    assert deviations
    assert all("MODEL REDLINE" not in (f.suggested_redline or "") for f in deviations)
