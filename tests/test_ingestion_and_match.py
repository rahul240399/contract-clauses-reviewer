from contract_review.datasets.contractnli import load_documents
from contract_review.models import Rule, Verdict
from contract_review.stages.match import match


def test_ingestion_builds_documents_with_round_tripping_spans(fixtures_data_dir):
    docs = load_documents("dev", data_dir=fixtures_data_dir)
    assert len(docs) == 1
    doc = docs[0]
    assert doc.id == "1"
    assert len(doc.spans) == 2
    # every span's text equals the slice its offsets point at
    assert all(s.text == doc.text[s.start : s.end] for s in doc.spans)


def test_match_returns_all_spans_as_id_tagged_context(fixtures_data_dir):
    doc = load_documents("dev", data_dir=fixtures_data_dir)[0]
    rule = Rule(id="nda-11", name="n", statement="s", expected_disposition=Verdict.ENTAILMENT)
    ctx = match(doc, rule)
    assert ctx.rule_id == "nda-11"
    assert ctx.candidate_span_ids == ["s0", "s1"]
    lines = ctx.context_text.splitlines()
    assert lines[0] == "[s0] No reverse engineering."
    assert lines[1].startswith("[s1] Obligations survive")
