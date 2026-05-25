"""Runtime configuration.

Single source of truth for the model, the verify/assess retry budget, and where
the API key comes from. No secrets live here — only the name of the env var to
read them from.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

API_KEY_ENV = "ANTHROPIC_API_KEY"


@dataclass(frozen=True)
class Settings:
    # Reasoning model used by the assess/verify stages. Configurable so we can
    # trade cost vs. capability per run.
    model: str = "claude-sonnet-4-6"
    # Extended-thinking budget for the assess stage (the hard reasoning step).
    max_thinking_tokens: int = 4000
    # How many times verify may bounce a failing assessment back to assess.
    max_assess_attempts: int = 2

    @property
    def api_key(self) -> str | None:
        return os.environ.get(API_KEY_ENV)

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)


def load_settings() -> Settings:
    return Settings()
