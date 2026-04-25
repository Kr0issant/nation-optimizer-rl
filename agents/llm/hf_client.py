"""Hugging Face client boundary for LLM adapters.

Tests use mock ``TextGenerationClient`` implementations. The concrete
``HuggingFaceTextGenerationClient`` imports provider dependencies lazily so CI
does not need Hugging Face credentials or network access.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

DEFAULT_MAX_NEW_TOKENS = 256


@dataclass(frozen=True, slots=True)
class TextGenerationResult:
    completion: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class TextGenerationClient(Protocol):
    def generate(self, prompt: str) -> str | TextGenerationResult:
        """Return a model completion for the provided prompt."""


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
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise ImportError(
                "Install huggingface_hub to use HuggingFaceTextGenerationClient."
            ) from exc

        self.model = model or os.environ.get("HF_MODEL_ID")
        if not self.model:
            raise ValueError("HF_MODEL_ID or model=... is required.")
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self._client = InferenceClient(
            model=self.model,
            token=token or os.environ.get("HF_TOKEN"),
        )

    def generate(self, prompt: str) -> TextGenerationResult:
        response = self._client.text_generation(
            prompt,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            details=True,
            return_full_text=False,
        )
        completion = str(getattr(response, "generated_text", response))
        details = getattr(response, "details", None)
        usage = _usage_from_details(details)
        return TextGenerationResult(completion=completion, **usage)


def _usage_from_details(details: Any) -> dict[str, int | None]:
    if details is None:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
    prompt_tokens = _count_tokens(getattr(details, "prefill", None))
    completion_tokens = _count_tokens(getattr(details, "tokens", None))
    total_tokens = (
        prompt_tokens + completion_tokens
        if prompt_tokens is not None and completion_tokens is not None
        else None
    )
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


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
