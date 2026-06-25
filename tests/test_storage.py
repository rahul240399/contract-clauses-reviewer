from contract_review.models import Finding, Report, Verdict
from contract_review.ports import ReviewRepository
from contract_review.storage import SQLiteReviewRepository


def _report():
    return Report(
        document_id="3",
        playbook_id="nda_contractnli",
        findings=[
            Finding(rule_id="nda-19", rule_name="Survival", expected=Verdict.ENTAILMENT,
                    actual=Verdict.CONTRADICTION, is_deviation=True, evidence_span_ids=["s71"])
        ],
        deviation_score=0.5,
    )


def test_sqlite_repo_satisfies_port(tmp_path):
    repo = SQLiteReviewRepository(tmp_path / "r.db")
    assert isinstance(repo, ReviewRepository)


def test_save_get_list_and_signoff(tmp_path):
    repo = SQLiteReviewRepository(tmp_path / "r.db")
    rid = repo.save(_report(), review_id="rev-1", created_at="2026-06-16T00:00:00Z")
    assert rid == "rev-1"
    got = repo.get("rev-1")
    assert got is not None and got.deviations[0].rule_id == "nda-19"
    assert repo.list_ids() == ["rev-1"]
    repo.set_signoff("rev-1", "approved")  # should not raise
    assert repo.get("missing") is None
