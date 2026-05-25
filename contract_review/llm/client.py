"""Thin wrapper over the Anthropic SDK for reasoning calls with structured output.

Status: stub. Centralizes model selection, extended thinking, structured-output
(tool-use) calls, and retry/backoff so the stages stay free of SDK details.
Implemented in a later step.
"""

from __future__ import annotations

from ..config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        raise NotImplementedError("LLMClient: implemented in a later step")
