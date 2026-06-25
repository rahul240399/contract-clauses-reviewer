import pytest

from contract_review.models import Verdict
from contract_review.playbook.loader import load_named, load_playbook


def test_bundled_nda_playbook_loads():
    pb = load_named("nda_contractnli")
    assert len(pb) == 17
    assert pb.rule_by_id("nda-19").expected_disposition is Verdict.ENTAILMENT
    assert pb.rule_by_id("nda-1").expected_disposition is Verdict.NOT_MENTIONED


def _write(tmp_path, text):
    path = tmp_path / "pb.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_invalid_disposition_rejected(tmp_path):
    bad = _write(tmp_path, """
id: x
name: X
rules:
  - id: r1
    name: n
    statement: s
    expected_disposition: Maybe
""")
    with pytest.raises(ValueError, match="invalid expected_disposition"):
        load_playbook(bad)


def test_duplicate_rule_id_rejected(tmp_path):
    bad = _write(tmp_path, """
id: x
name: X
rules:
  - id: r1
    name: n
    statement: s
    expected_disposition: Entailment
  - id: r1
    name: m
    statement: t
    expected_disposition: NotMentioned
""")
    with pytest.raises(ValueError, match="duplicate rule id"):
        load_playbook(bad)


def test_missing_key_rejected(tmp_path):
    bad = _write(tmp_path, """
id: x
name: X
rules:
  - id: r1
    name: n
    expected_disposition: Entailment
""")
    with pytest.raises(ValueError, match="missing required key"):
        load_playbook(bad)
