"""LLM adapter for any OpenAI-compatible /chat/completions endpoint.

Talks to a local Ollama server (default), vLLM, LM Studio, llama.cpp, or a hosted
open-model API - using plain httpx against the de-facto-standard wire format, not
a vendor SDK. Implements the two LLM-port primitives:

- think():   a normal completion that returns free-form reasoning text.
- extract(): a completion that forces a tool call and returns its parsed arguments.
"""

from __future__ import annotations

import json

import httpx

from ..config import Settings


class OpenAICompatibleLLM:
    def __init__(self, settings: Settings) -> None:
        self._url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        self._model = settings.llm_model
        self._headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = settings.request_timeout_s

    def _post(self, payload: dict) -> dict:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self._url, json=payload, headers=self._headers)
            response.raise_for_status()
            return response.json()

    def think(self, *, system: str, prompt: str, max_thinking_tokens: int) -> str:
        data = self._post(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_thinking_tokens,
                "temperature": 0.0,
            }
        )
        return data["choices"][0]["message"].get("content") or ""

    def extract(self, *, system: str, prompt: str, tool: dict, tool_name: str) -> dict:
        data = self._post(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "tools": [{"type": "function", "function": tool}],
                "tool_choice": {"type": "function", "function": {"name": tool_name}},
                "temperature": 0.0,
            }
        )
        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            raise ValueError("model returned no tool call for forced extraction")
        arguments = tool_calls[0]["function"]["arguments"]
        return json.loads(arguments) if isinstance(arguments, str) else arguments
