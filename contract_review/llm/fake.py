"""A deterministic LLM port implementation for development and tests.

Lets the entire core run end-to-end with no model, no API key, and no network.
Configure `extract_fn` to drive verdicts from the prompt (e.g. to replay gold
answers), or rely on the default. Calls are recorded for assertions.
"""

from __future__ import annotations

import threading
from typing import Callable

ExtractFn = Callable[..., dict]


class FakeLLM:
    def __init__(
        self,
        *,
        extract_fn: ExtractFn | None = None,
        default_extract: dict | None = None,
        think_text: str = "(fake reasoning)",
    ) -> None:
        self._extract_fn = extract_fn
        self._default_extract = default_extract or {
            "verdict": "NotMentioned",
            "evidence_span_ids": [],
            "rationale": "fake default",
        }
        self._think_text = think_text
        # The pipeline assesses rules concurrently, so guard the call log.
        self._lock = threading.Lock()
        self.calls: list[tuple[str, str]] = []

    def think(self, *, system: str, prompt: str, max_thinking_tokens: int) -> str:
        with self._lock:
            self.calls.append(("think", prompt))
        return self._think_text

    def extract(self, *, system: str, prompt: str, tool: dict, tool_name: str) -> dict:
        with self._lock:
            self.calls.append(("extract", prompt))
        if self._extract_fn is not None:
            return self._extract_fn(prompt=prompt, tool=tool, tool_name=tool_name)
        return dict(self._default_extract)
