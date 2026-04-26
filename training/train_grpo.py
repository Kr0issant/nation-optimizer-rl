"""GRPO fine-tune for the parliamentary minister adapter.

Designed to run identically on a laptop (``--smoke``) and on Hugging Face Jobs
via ``hf jobs uv run``::

    hf jobs uv run --flavor a10g-small --secrets HF_TOKEN \
        training/train_grpo.py \
        --dataset-id <user>/nation-parliamentary-prompts \
        --hub-model-id <user>/nation-parliamentary-grpo-lora

The reward signal is the dense, env-grounded
:func:`training.reward_fn.make_reward_fn`. Training uses LoRA on top of
``Qwen/Qwen2.5-0.5B-Instruct``. Logging goes to Trackio so the README can link
the training curve directly.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "trl>=0.20",
#     "peft>=0.12",
#     "datasets>=2.20",
#     "transformers>=4.44",
#     "trackio>=0.1",
#     "accelerate>=0.34",
#     "bitsandbytes>=0.43",
#     "huggingface-hub>=1.12",
#     "pydantic>=2.13",
# ]
# ///

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Debug: show where we are and what we see
print(f"DEBUG: CWD={os.getcwd()}")
print(f"DEBUG: Files in CWD={os.listdir('.')}")
print(f"DEBUG: __file__={__file__}")

# Ensure project root is in sys.path for HF Jobs
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
print(f"DEBUG: sys.path={sys.path}")


DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
# Regenerate with `python -m scripts.collect_grpo_prompts` after game/economy changes.
DEFAULT_DATASET_ID = "nation-optimizer/nation-parliamentary-prompts"
DEFAULT_HUB_MODEL_ID = "nation-optimizer/nation-parliamentary-grpo-lora"


@dataclass(frozen=True, slots=True)
class TrainArgs:
    base_model: str
    dataset_id: str
    dataset_split: str
    output_dir: str
    hub_model_id: str | None
    push_to_hub: bool
    max_steps: int
    learning_rate: float
    per_device_batch_size: int
    num_generations: int
    max_prompt_length: int
    max_completion_length: int
    beta: float
    bf16: bool
    fp16: bool
    smoke: bool
    seed: int
    report_to: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument("--dataset-split", default="train")
    parser.add_argument("--output-dir", default="./out/grpo")
    parser.add_argument("--hub-model-id", default=DEFAULT_HUB_MODEL_ID)
    parser.add_argument("--no-push", action="store_true", help="Disable push_to_hub.")
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--per-device-batch-size", type=int, default=4)
    parser.add_argument("--num-generations", type=int, default=4)
    parser.add_argument("--max-prompt-length", type=int, default=2048)
    parser.add_argument("--max-completion-length", type=int, default=256)
    parser.add_argument("--beta", type=float, default=0.04)
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--no-bf16", dest="bf16", action="store_false")
    parser.add_argument("--fp16", action="store_true", default=False)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help=(
            "Tiny CPU-friendly run: 5 steps, batch=1, no push, fp32. "
            "Proves the pipeline imports and the reward function can score "
            "real generations end-to-end without a GPU."
        ),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--report-to",
        default="trackio",
        help="Pass to TrainingArguments.report_to; use 'none' to disable.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> TrainArgs:
    args = build_parser().parse_args(argv)
    return TrainArgs(
        base_model=args.base_model,
        dataset_id=args.dataset_id,
        dataset_split=args.dataset_split,
        output_dir=args.output_dir,
        hub_model_id=args.hub_model_id if not args.no_push else None,
        push_to_hub=not args.no_push,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        per_device_batch_size=args.per_device_batch_size,
        num_generations=args.num_generations,
        max_prompt_length=args.max_prompt_length,
        max_completion_length=args.max_completion_length,
        beta=args.beta,
        bf16=args.bf16,
        fp16=args.fp16,
        smoke=args.smoke,
        seed=args.seed,
        report_to=args.report_to,
    )


def apply_smoke_overrides(cfg: TrainArgs) -> TrainArgs:
    """Force a tiny CPU-friendly configuration for the ``--smoke`` flag."""
    if not cfg.smoke:
        return cfg
    return TrainArgs(
        base_model=cfg.base_model,
        dataset_id=cfg.dataset_id,
        dataset_split=cfg.dataset_split,
        output_dir=cfg.output_dir,
        hub_model_id=None,
        push_to_hub=False,
        max_steps=5,
        learning_rate=cfg.learning_rate,
        per_device_batch_size=1,
        num_generations=2,
        max_prompt_length=512,
        max_completion_length=64,
        beta=cfg.beta,
        bf16=False,
        fp16=False,
        smoke=True,
        seed=cfg.seed,
        report_to="none",
    )


def main(argv: list[str] | None = None) -> int:
    cfg = apply_smoke_overrides(parse_args(argv))

    try:
        from datasets import load_dataset
        from peft import LoraConfig
        from trl import GRPOConfig, GRPOTrainer
    except ImportError as exc:  # pragma: no cover - exercised on real GPUs only
        print(
            "Missing training extras. Install with: "
            "pip install -e '.[training]' "
            f"(import error: {exc})",
            file=sys.stderr,
        )
        return 2

    from training.reward_fn import make_reward_fn

    print(
        f"[train_grpo] base={cfg.base_model} dataset={cfg.dataset_id} "
        f"steps={cfg.max_steps} batch={cfg.per_device_batch_size} "
        f"G={cfg.num_generations} smoke={cfg.smoke}"
    )

    dataset = load_dataset(cfg.dataset_id, split=cfg.dataset_split)
    if cfg.smoke:
        dataset = dataset.select(range(min(8, len(dataset))))

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    grpo_config = GRPOConfig(
        output_dir=cfg.output_dir,
        learning_rate=cfg.learning_rate,
        per_device_train_batch_size=cfg.per_device_batch_size,
        num_generations=cfg.num_generations,
        max_prompt_length=cfg.max_prompt_length,
        max_completion_length=cfg.max_completion_length,
        max_steps=cfg.max_steps,
        logging_steps=1 if cfg.smoke else 10,
        save_steps=cfg.max_steps,
        bf16=cfg.bf16,
        fp16=cfg.fp16,
        report_to=cfg.report_to,
        push_to_hub=cfg.push_to_hub,
        hub_model_id=cfg.hub_model_id,
        beta=cfg.beta,
        seed=cfg.seed,
    )

    trainer = GRPOTrainer(
        model=cfg.base_model,
        reward_funcs=make_reward_fn(),
        args=grpo_config,
        train_dataset=dataset,
        peft_config=lora_config,
    )
    trainer.train()
    if cfg.push_to_hub and cfg.hub_model_id:
        trainer.push_to_hub()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
