"""Ports: the interfaces the domain core depends on.

The core (stages, pipeline) depends only on these Protocols, never on a concrete
SDK, database, or transport. Adapters (the anthropic client, the SQLite repo, the
ContractNLI/PDF loaders) implement them. This is what keeps the core testable
without an API key and the system deployable with swappable parts.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import Document, Report


@runtime_checkable
class LLM(Protocol):
    """Reasoning-model boundary used by the assess (and optionally verify) stage.

    Two primitives mirror the two-step assess design: a free-form reasoning pass
    (extended thinking, no tools) and a forced structured extraction (a tool call
    whose validated arguments are returned as a dict).
    """

    def think(self, *, system: str, prompt: str, max_thinking_tokens: int) -> str: ...

    def extract(
        self, *, system: str, prompt: str, tool: dict, tool_name: str
    ) -> dict: ...


@runtime_checkable
class DocumentSource(Protocol):
    """Where a contract to review comes from (ContractNLI now, PDF/upload later)."""

    def load(self, ref: str) -> Document: ...


@runtime_checkable
class ReviewRepository(Protocol):
    """Persistence boundary for completed reviews (the audit trail)."""

    def save(self, report: Report) -> str: ...

    def get(self, review_id: str) -> Report | None: ...

    def list_ids(self) -> list[str]: ...

    def set_signoff(self, review_id: str, status: str) -> None: ...
