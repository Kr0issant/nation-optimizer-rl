"""Local ``transformers`` text-generation client with optional LoRA adapter.

Used by :mod:`evaluation.benchmark_policies` to evaluate the trained
parliamentary adapter on CPU/GPU without going through the HF Inference API.
``transformers`` and ``peft`` are imported lazily so that pytest collection on
machines without the training extras installed still works.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

from llm_integration.hf_client import TextGenerationResult

DEFAULT_MAX_NEW_TOKENS = 256
DEFAULT_TEMPERATURE = 0.2


class LocalTransformersClient:
    """``TextGenerationClient`` backed by a locally loaded HF model.

    Parameters
    ----------
    model:
        HF Hub model id of the base causal LM (e.g.
        ``"Qwen/Qwen2.5-0.5B-Instruct"``).
    lora:
        Optional HF Hub repo or local path of a PEFT/LoRA adapter to apply on
        top of the base model. When ``None`` the bare base model is used.
    device:
        Override the device. Defaults to ``"cuda"`` if available, else ``"cpu"``.
    dtype:
        Override the model dtype. ``None`` defers to ``transformers``' default,
        which is bf16 on Ampere+ GPUs.
    """

    def __init__(
        self,
        model: str,
        *,
        lora: str | None = None,
        device: str | None = None,
        dtype: Any = None,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        do_sample: bool | None = None,
    ) -> None:
        self.model_id = model
        self.lora_id = lora
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.do_sample = do_sample if do_sample is not None else temperature > 0.0

        transformers = import_module("transformers")
        torch = import_module("torch")

        resolved_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.device = resolved_device

        token = os.environ.get("HF_TOKEN")
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(model, token=token)
        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        load_kwargs: dict[str, Any] = {"token": token}
        if dtype is not None:
            load_kwargs["torch_dtype"] = dtype

        base_model = transformers.AutoModelForCausalLM.from_pretrained(
            model,
            **load_kwargs,
        )

        if lora:
            peft = import_module("peft")
            base_model = peft.PeftModel.from_pretrained(base_model, lora, token=token)

        self.model = base_model.to(resolved_device)
        self.model.eval()

    def generate(self, prompt: str) -> TextGenerationResult:
        torch = import_module("torch")

        messages = [{"role": "user", "content": prompt}]
        chat_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(chat_text, return_tensors="pt").to(self.device)
        prompt_tokens = int(inputs["input_ids"].shape[1])

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature if self.do_sample else 1.0,
                do_sample=self.do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        completion_tokens = int(outputs.shape[1] - prompt_tokens)
        completion = self.tokenizer.decode(
            outputs[0, prompt_tokens:],
            skip_special_tokens=True,
        )
        return TextGenerationResult(
            completion=completion,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )


__all__ = ["LocalTransformersClient"]
