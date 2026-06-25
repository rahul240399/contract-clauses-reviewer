"""Contract ingestion: turn a file on disk into a segmented Document.

Dispatches by file extension - PDFs are run through a text extractor, everything
else is read as UTF-8 text - then handed to the segmenter. PDF support is an
optional dependency (pypdf); it is imported lazily so the core has no hard
dependency on it, and a missing install yields a clear, actionable error.
"""

from __future__ import annotations

from pathlib import Path

from .models import Document
from .stages.segment import segment


def extract_pdf_text(path: str | Path) -> str:
    """Extract text from a PDF, joining pages with blank lines."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "PDF support requires pypdf. Install it with: pip install 'contract-review[pdf]'"
        ) from exc

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(p for p in pages if p)


def read_contract_text(path: str | Path) -> str:
    """Read a contract file to plain text, extracting from PDF when needed."""
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    return path.read_text(encoding="utf-8")


def load_contract(
    path: str | Path,
    *,
    doc_id: str | None = None,
    source_name: str | None = None,
) -> Document:
    """Read and segment a contract file (text or PDF) into a Document."""
    path = Path(path)
    text = read_contract_text(path)
    return segment(text, source_name=source_name or str(path), doc_id=doc_id or str(path))
