"""Hugging Face client boundary for LLM adapters.

Tests use mock ``TextGenerationClient`` implementations. The concrete
``HuggingFaceTextGenerationClient`` imports provider dependencies lazily so CI
does not need Hugging Face credentials or network access.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol

DEFAULT_MAX_NEW_TOKENS = 256


@dataclass(frozen=True, slots=True)
class TextGenerationResult:
    completion: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class TextGenerationClient(Protocol):
    def generate(self, prompt: str) -> str | TextGenerationResult: ...


class HuggingFaceTextGenerationClient:
    """Optional Hugging Face Inference API implementation.

    Requires ``huggingface_hub`` to be installed and reads ``HF_TOKEN`` plus
    ``HF_MODEL_ID`` by default. Unit tests should mock ``TextGenerationClient``
    instead of constructing this class.
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        token: str | None = None,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        temperature: float = 0.2,
    ) -> None:
        try:
            huggingface_hub = import_module("huggingface_hub")
        except ImportError as exc:
            raise ImportError(
                "Install huggingface_hub to use HuggingFaceTextGenerationClient."
            ) from exc

        self.model = model or os.environ.get("HF_MODEL_ID")
        if not self.model:
            raise ValueError("HF_MODEL_ID or model=... is required.")
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self._client = huggingface_hub.InferenceClient(
            model=self.model,
            token=token or os.environ.get("HF_TOKEN"),
        )

    def generate(self, prompt: str) -> TextGenerationResult:
        messages = [{"role": "user", "content": prompt}]
        response = self._client.chat_completion(
            messages=messages,
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
        )
        completion = response.choices[0].message.content
        if completion is None:
            completion = ""
        
        usage_obj = getattr(response, "usage", None)
        usage = {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", None),
            "completion_tokens": getattr(usage_obj, "completion_tokens", None),
            "total_tokens": getattr(usage_obj, "total_tokens", None),
        }
        return TextGenerationResult(completion=completion, **usage)


def _count_tokens(tokens: Any) -> int | None:
    if tokens is None:
        return None
    try:
        return len(tokens)
    except TypeError:
        return None


__all__ = [
    "HuggingFaceTextGenerationClient",
    "TextGenerationClient",
    "TextGenerationResult",
]
