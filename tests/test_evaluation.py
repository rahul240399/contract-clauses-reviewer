from contract_review.models import Assessment, Verdict
from evaluation.metrics import evaluate, evidence_prf, verdict_macro_f1
from evaluation.oracle import load_gold


def test_oracle_loads_gold_with_mapped_span_ids(fixtures_data_dir):
    gold = load_gold("dev", data_dir=fixtures_data_dir)
    assert set(gold) == {"1"}
    doc = gold["1"]
    assert doc["nda-11"].verdict is Verdict.ENTAILMENT
    assert doc["nda-11"].evidence_span_ids == ["s0"]
    assert doc["nda-7"].verdict is Verdict.NOT_MENTIONED
    assert doc["nda-7"].evidence_span_ids == []


def _pairs_from_gold(gold_doc, *, perfect=True):
    pairs = []
    for rid, g in gold_doc.items():
        if perfect:
            pred = Assessment(rule_id=rid, verdict=g.verdict, evidence_span_ids=list(g.evidence_span_ids))
        else:
            pred = Assessment(rule_id=rid, verdict=Verdict.NOT_MENTIONED, evidence_span_ids=[])
        pairs.append((pred, g))
    return pairs


def test_perfect_predictions_score_one(fixtures_data_dir):
    gold = load_gold("dev", data_dir=fixtures_data_dir)["1"]
    res = evaluate(_pairs_from_gold(gold, perfect=True))
    assert res.verdict_accuracy == 1.0
    assert res.evidence_f1 == 1.0


def test_lazy_baseline_loses_on_macro_f1(fixtures_data_dir):
    gold = load_gold("dev", data_dir=fixtures_data_dir)["1"]
    perfect = verdict_macro_f1(_pairs_from_gold(gold, perfect=True))
    lazy = verdict_macro_f1(_pairs_from_gold(gold, perfect=False))
    assert lazy < perfect


def test_evidence_prf_partial_overlap():
    from evaluation.oracle import GoldAnnotation

    gold = GoldAnnotation(rule_id="r", verdict=Verdict.ENTAILMENT, evidence_span_ids=["s1", "s2"])
    pred = Assessment(rule_id="r", verdict=Verdict.ENTAILMENT, evidence_span_ids=["s1", "s9"])
    precision, recall, f1 = evidence_prf([(pred, gold)])
    assert precision == 0.5  # 1 of 2 predicted are correct
    assert recall == 0.5  # 1 of 2 gold recovered
