from starlette.testclient import TestClient

from contract_review.api import create_app
from contract_review.storage import SQLiteReviewRepository


def _client(tmp_path):
    repo = SQLiteReviewRepository(tmp_path / "api.db")
    return TestClient(create_app(repo=repo))


def test_health(tmp_path):
    assert _client(tmp_path).get("/health").json() == {"status": "ok"}


def test_review_text_then_fetch_and_signoff(tmp_path):
    client = _client(tmp_path)

    resp = client.post("/reviews", json={
        "text": "The Receiving Party shall not reverse engineer the product.",
        "offline": True,
    })
    assert resp.status_code == 200
    body = resp.json()
    review_id = body["review_id"]
    assert len(body["report"]["findings"]) == 17
    assert 0.0 <= body["report"]["deviation_score"] <= 1.0

    # listed + fetchable
    assert review_id in client.get("/reviews").json()["review_ids"]
    assert client.get(f"/reviews/{review_id}").json()["document_id"] == "uploaded"

    # sign-off
    assert client.post(f"/reviews/{review_id}/signoff", json={"status": "approved"}).status_code == 200


def test_missing_input_is_422(tmp_path):
    assert _client(tmp_path).post("/reviews", json={"offline": True}).status_code == 422


def test_upload_text_file(tmp_path):
    client = _client(tmp_path)
    resp = client.post(
        "/reviews/upload",
        files={"file": ("nda.txt", b"The Receiving Party shall not reverse engineer.", "text/plain")},
        data={"offline": "true"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["report"]["findings"]) == 17
    assert body["report"]["document_id"] == "nda.txt"
    assert body["review_id"] in client.get("/reviews").json()["review_ids"]


def test_upload_pdf_file(tmp_path):
    import pytest

    pytest.importorskip("pypdf", reason="PDF support not installed")
    from tests.test_ingest import _make_pdf

    client = _client(tmp_path)
    pdf = _make_pdf(["The Receiving Party shall not reverse engineer the product.",
                     "Confidentiality obligations survive termination."])
    resp = client.post(
        "/reviews/upload",
        files={"file": ("nda.pdf", pdf, "application/pdf")},
        data={"offline": "true"},
    )
    assert resp.status_code == 200
    assert resp.json()["report"]["document_id"] == "nda.pdf"


def test_unknown_review_is_404(tmp_path):
    assert _client(tmp_path).get("/reviews/nope").status_code == 404


def test_get_playbook(tmp_path):
    resp = _client(tmp_path).get("/playbooks/nda_contractnli")
    assert resp.status_code == 200
    assert len(resp.json()["rules"]) == 17
