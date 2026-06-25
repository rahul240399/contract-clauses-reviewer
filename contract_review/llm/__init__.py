"""LLM adapters implementing the LLM port.

OpenAICompatibleLLM talks to any OpenAI-compatible endpoint (local Ollama, vLLM,
LM Studio, llama.cpp, or a hosted open-model API). FakeLLM is a deterministic
stand-in for development and tests.
"""

from .fake import FakeLLM
from .openai_compatible import OpenAICompatibleLLM

__all__ = ["FakeLLM", "OpenAICompatibleLLM"]
