from contract_review.cli import main
from contract_review.stages.segment import segment


def test_segment_offsets_round_trip():
    text = "First clause here. Second one.\nThird on a new line."
    doc = segment(text, source_name="x", doc_id="x")
    assert len(doc.spans) == 3
    # every span's text matches the slice its offsets point at
    assert all(s.text == doc.text[s.start : s.end] for s in doc.spans)
    assert doc.spans[0].text == "First clause here."
    assert doc.spans[2].text == "Third on a new line."


def test_segment_skips_blank_segments():
    doc = segment("A.\n\n\nB.", source_name="x", doc_id="x")
    assert [s.text for s in doc.spans] == ["A.", "B."]


def test_cli_review_runs_end_to_end_offline(tmp_path, capsys):
    contract = tmp_path / "nda.txt"
    contract.write_text("The Receiving Party shall not reverse engineer the product.")
    rc = main(["review", "--file", str(contract), "--offline"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Deviation score:" in out
    assert "nda-19" in out  # the playbook rules are listed
