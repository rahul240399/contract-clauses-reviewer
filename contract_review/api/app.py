"""FastAPI service: the deployable surface, a thin shell over the core pipeline.

Endpoints:
  GET  /health
  POST /reviews                  run a review, persist it, return {review_id, report}
  GET  /reviews                  list review ids
  GET  /reviews/{id}             fetch a stored report
  POST /reviews/{id}/signoff     record human sign-off
  GET  /playbooks/{name}         inspect a rubric

The service reuses the same pipeline, playbook loader, and repository as the CLI;
nothing domain-specific lives here. `use_fake` runs the deterministic FakeLLM so
the API is usable (and testable) without a model.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ..config import Settings, load_settings
from ..datasets.contractnli import load_documents
from ..llm import FakeLLM, OpenAICompatibleLLM
from ..models import Document, Report
from ..pipeline import review as run_pipeline
from ..playbook.loader import load_named
from ..ports import ReviewRepository
from ..stages.segment import segment
from ..storage import SQLiteReviewRepository


class ReviewRequest(BaseModel):
    text: str | None = None
    contractnli_id: str | None = None
    split: str = "dev"
    playbook: str = "nda_contractnli"
    use_fake: bool = False


class SignoffRequest(BaseModel):
    status: str


def _load_document(req: ReviewRequest) -> Document:
    if req.text is not None:
        return segment(req.text, source_name="uploaded", doc_id="uploaded")
    if req.contractnli_id is not None:
        for doc in load_documents(req.split):
            if doc.id == str(req.contractnli_id):
                return doc
        raise HTTPException(404, f"document {req.contractnli_id} not in {req.split} split")
    raise HTTPException(422, "provide either 'text' or 'contractnli_id'")


def create_app(
    repo: ReviewRepository | None = None, settings: Settings | None = None
) -> FastAPI:
    settings = settings or load_settings()
    repo = repo or SQLiteReviewRepository("reviews.db")
    app = FastAPI(title="Contract Clause Reviewer")

    def build_llm(use_fake: bool):
        return FakeLLM() if use_fake else OpenAICompatibleLLM(settings)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/reviews")
    def create_review(req: ReviewRequest) -> dict:
        document = _load_document(req)
        try:
            playbook = load_named(req.playbook)
        except FileNotFoundError:
            raise HTTPException(404, f"playbook {req.playbook!r} not found")
        report = run_pipeline(document, playbook, build_llm(req.use_fake), settings=settings)
        review_id = repo.save(report)
        return {"review_id": review_id, "report": report.model_dump()}

    @app.get("/reviews")
    def list_reviews() -> dict:
        return {"review_ids": repo.list_ids()}

    @app.get("/reviews/{review_id}")
    def get_review(review_id: str) -> Report:
        report = repo.get(review_id)
        if report is None:
            raise HTTPException(404, "review not found")
        return report

    @app.post("/reviews/{review_id}/signoff")
    def signoff(review_id: str, body: SignoffRequest) -> dict:
        if repo.get(review_id) is None:
            raise HTTPException(404, "review not found")
        repo.set_signoff(review_id, body.status)
        return {"review_id": review_id, "signoff_status": body.status}

    @app.get("/playbooks/{name}")
    def get_playbook(name: str):
        try:
            return load_named(name)
        except FileNotFoundError:
            raise HTTPException(404, "playbook not found")

    return app


app = create_app()
