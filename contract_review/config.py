"""Runtime configuration via environment variables (12-factor).

Single source of truth for the model, the verify/assess retry budget, and the
API key. No secrets are hard-coded; they are read from the environment (or a
local .env file). Settings are validated by pydantic-settings at load time.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Read straight from ANTHROPIC_API_KEY (the SDK's conventional name).
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

    # Reasoning model for the assess/verify stages; override via CONTRACT_REVIEW_MODEL.
    model: str = Field(default="claude-sonnet-4-6", validation_alias="CONTRACT_REVIEW_MODEL")
    # Extended-thinking budget for the assess "think" step.
    max_thinking_tokens: int = Field(
        default=4000, validation_alias="CONTRACT_REVIEW_MAX_THINKING_TOKENS"
    )
    # How many times verify may bounce a failing assessment back to assess.
    max_assess_attempts: int = Field(
        default=2, validation_alias="CONTRACT_REVIEW_MAX_ASSESS_ATTEMPTS"
    )
    # Cap on concurrent per-rule assess calls.
    assess_concurrency: int = Field(
        default=8, validation_alias="CONTRACT_REVIEW_ASSESS_CONCURRENCY"
    )

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key)


def load_settings() -> Settings:
    return Settings()
