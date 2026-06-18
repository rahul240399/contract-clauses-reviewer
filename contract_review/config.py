"""Runtime configuration via environment variables (12-factor).

The reasoning model is any OpenAI-compatible endpoint: a local Ollama server
(default), vLLM, LM Studio, llama.cpp, or a hosted open-model API. No paid
service is required; defaults target a local Ollama install running an
open-source model.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI-compatible endpoint. Ollama's default is http://localhost:11434/v1.
    llm_base_url: str = Field(
        default="http://localhost:11434/v1", validation_alias="LLM_BASE_URL"
    )
    # Open-source model name as the server knows it (e.g. an Ollama tag).
    llm_model: str = Field(default="qwen2.5:7b", validation_alias="LLM_MODEL")
    # Most local servers ignore the key, but the field is often required to be non-empty.
    llm_api_key: str = Field(default="not-needed", validation_alias="LLM_API_KEY")
    request_timeout_s: float = Field(default=120.0, validation_alias="LLM_TIMEOUT_S")

    # Token budget for the assess "think" (reasoning) step.
    max_reasoning_tokens: int = Field(
        default=1024, validation_alias="CONTRACT_REVIEW_MAX_REASONING_TOKENS"
    )
    # How many times verify may bounce a failing assessment back to assess.
    max_assess_attempts: int = Field(
        default=2, validation_alias="CONTRACT_REVIEW_MAX_ASSESS_ATTEMPTS"
    )
    # Cap on concurrent per-rule assess calls.
    assess_concurrency: int = Field(
        default=4, validation_alias="CONTRACT_REVIEW_ASSESS_CONCURRENCY"
    )


def load_settings() -> Settings:
    return Settings()
