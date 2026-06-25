import pytest

from contract_review.ingest import load_contract, read_contract_text

pytest.importorskip("pypdf", reason="PDF support (pdf extra) not installed")


def _make_pdf(lines: list[str]) -> bytes:
    """A minimal valid single-page PDF whose content stream prints `lines`."""
    ops = "BT /F1 12 Tf 72 720 Td 14 TL\n" + "".join(f"({l}) Tj T*\n" for l in lines) + "ET"
    objs = [
        "<</Type/Catalog/Pages 2 0 R>>",
        "<</Type/Pages/Kids[3 0 R]/Count 1>>",
        "<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R"
        "/Resources<</Font<</F1 5 0 R>>>>>>",
        f"<</Length {len(ops)}>>\nstream\n{ops}\nendstream",
        "<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    out = "%PDF-1.4\n"
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n"
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<</Size {len(objs)+1}/Root 1 0 R>>\nstartxref\n{xref_pos}\n%%EOF"
    return out.encode("latin-1")


def test_read_pdf_extracts_text(tmp_path):
    pdf = tmp_path / "nda.pdf"
    pdf.write_bytes(_make_pdf(["The Receiving Party shall not reverse engineer.",
                               "Confidentiality obligations survive termination."]))
    text = read_contract_text(pdf)
    assert "reverse engineer" in text
    assert "survive termination" in text


def test_load_pdf_segments_into_spans(tmp_path):
    pdf = tmp_path / "nda.pdf"
    pdf.write_bytes(_make_pdf(["The Receiving Party shall not reverse engineer.",
                               "Confidentiality obligations survive termination."]))
    doc = load_contract(pdf)
    assert len(doc.spans) >= 2
    # spans resolve back to the document text via their offsets
    assert all(doc.text[s.start:s.end] == s.text for s in doc.spans)
    assert any("reverse engineer" in s.text for s in doc.spans)


def test_txt_path_still_reads_as_text(tmp_path):
    txt = tmp_path / "nda.txt"
    txt.write_text("No reverse engineering. Obligations survive termination.")
    doc = load_contract(txt)
    assert len(doc.spans) == 2
    assert read_contract_text(txt).startswith("No reverse engineering")
