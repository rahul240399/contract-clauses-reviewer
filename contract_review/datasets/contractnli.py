"""Load ContractNLI into the core Document model.

ContractNLI ships each contract already segmented into spans (character-offset
pairs). During development we treat these gold spans as the output of the segment
stage (a real text/PDF segmenter is added before contract upload is supported,
per the project's staging decision).

Gold *annotations* (the verdict/evidence answer key) are intentionally NOT loaded
here. They belong to the evaluation oracle, so the review path never sees the
answers it is meant to predict.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Document, Span

DEFAULT_DATA_DIR = Path(".scratch/contract-nli")
_SPLIT_FILES = {"train": "train.json", "dev": "dev.json", "test": "test.json"}


def _resolve_data_dir(data_dir: str | Path | None) -> Path:
    directory = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
    if not directory.exists():
        raise FileNotFoundError(
            f"ContractNLI not found at {directory}. "
            f"Run scripts/fetch_contractnli.sh first."
        )
    return directory


def load_raw_split(split: str, data_dir: str | Path | None = None) -> dict:
    """Return the parsed JSON for a split (documents + labels)."""
    if split not in _SPLIT_FILES:
        raise ValueError(f"unknown split {split!r}; choose from {list(_SPLIT_FILES)}")
    path = _resolve_data_dir(data_dir) / _SPLIT_FILES[split]
    return json.loads(path.read_text(encoding="utf-8"))


def to_document(raw_doc: dict) -> Document:
    """Convert one ContractNLI document record into a Document with gold spans."""
    text = raw_doc["text"]
    spans = [
        Span(id=f"s{i}", start=int(start), end=int(end), text=text[int(start) : int(end)])
        for i, (start, end) in enumerate(raw_doc["spans"])
    ]
    return Document(
        id=str(raw_doc["id"]),
        source_name=str(raw_doc.get("file_name", raw_doc["id"])),
        text=text,
        spans=spans,
    )


def load_documents(split: str, data_dir: str | Path | None = None) -> list[Document]:
    """Load all documents in a split as Document objects (gold spans, no labels)."""
    raw = load_raw_split(split, data_dir)
    return [to_document(doc) for doc in raw["documents"]]
