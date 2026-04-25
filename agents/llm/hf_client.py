"""Hugging Face client boundary for LLM adapters.

The concrete provider is intentionally deferred so tests can exercise adapters
without spending hosted inference or training credits.
"""

from typing import Protocol


class TextGenerationClient(Protocol):
    def generate(self, prompt: str) -> str:
        """Return a model completion for the provided prompt."""
