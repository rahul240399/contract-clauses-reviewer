"""LLM adapters implementing the LLM port.

OpenAICompatibleLLM talks to any OpenAI-compatible endpoint (local Ollama, vLLM,
LM Studio, llama.cpp, or a hosted open-model API). ScriptedLLM is a deterministic
stand-in for development and tests.
"""

from .openai_compatible import OpenAICompatibleLLM
from .scripted import ScriptedLLM

__all__ = ["OpenAICompatibleLLM", "ScriptedLLM"]
