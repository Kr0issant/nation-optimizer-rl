"""Plot benchmark summaries for hackathon evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def plot_benchmark_file(input_path: Path | str, output_dir: Path | str) -> list[Path]:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    return plot_benchmark_payload(payload, output_dir)


def plot_benchmark_payload(payload: dict[str, Any], output_dir: Path | str) -> list[Path]:
    import matplotlib.pyplot as plt

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    policies = [policy["policy"] for policy in payload["policies"]]
    mean_returns = [
        policy["summary"]["mean_episode_return"]
        for policy in payload["policies"]
    ]
    survival_rounds = [
        policy["summary"]["mean_survival_rounds"]
        for policy in payload["policies"]
    ]

    written_paths = [
        _write_bar_chart(
            plt=plt,
            labels=policies,
            values=mean_returns,
            title="Mean Episode Return by Baseline",
            ylabel="Mean episode return",
            output_path=output_path / "baseline_mean_episode_return.png",
        ),
        _write_bar_chart(
            plt=plt,
            labels=policies,
            values=survival_rounds,
            title="Survival Rounds by Baseline",
            ylabel="Mean survival rounds",
            output_path=output_path / "baseline_survival_rounds.png",
        ),
    ]
    plt.close("all")
    return written_paths


def plot_policy_comparison(
    payload: dict[str, Any],
    output_dir: Path | str,
    *,
    filename: str = "policy_comparison.png",
) -> Path:
    """Bar chart of mean episode return per policy, highlighting LLM variants.

    Used for the "before vs after" GRPO evidence in the README. The trained
    parliamentary LoRA bar is colour-coded so reviewers can spot the lift over
    the untrained base model and rule-based baselines at a glance.
    """
    import matplotlib.pyplot as plt

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    policies = [policy["policy"] for policy in payload["policies"]]
    mean_returns = [
        policy["summary"]["mean_episode_return"]
        for policy in payload["policies"]
    ]
    colors = [_policy_color(name) for name in policies]

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(policies, mean_returns, color=colors)
    axis.set_title("Mean Episode Return by Policy (rule-based vs LLM)")
    axis.set_xlabel("Policy")
    axis.set_ylabel("Mean episode return")
    axis.tick_params(axis="x", labelrotation=25)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    written = output_path / filename
    figure.savefig(written, dpi=160)
    plt.close(figure)
    return written


def plot_survival_rounds(
    payload: dict[str, Any],
    output_dir: Path | str,
    *,
    filename: str = "survival_rounds.png",
) -> Path:
    """Per-policy survival distribution box-plot from raw episode metrics."""
    import matplotlib.pyplot as plt

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    labels: list[str] = []
    distributions: list[list[float]] = []
    for policy in payload["policies"]:
        survivals = [
            float(episode["rounds_survived"])
            for episode in policy.get("episodes", [])
        ]
        if not survivals:
            survivals = [float(policy["summary"]["mean_survival_rounds"])]
        labels.append(policy["policy"])
        distributions.append(survivals)

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.boxplot(distributions, tick_labels=labels, showmeans=True)
    axis.set_title("Survival Rounds Distribution by Policy")
    axis.set_xlabel("Policy")
    axis.set_ylabel("Rounds survived")
    axis.tick_params(axis="x", labelrotation=25)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    written = output_path / filename
    figure.savefig(written, dpi=160)
    plt.close(figure)
    return written


def _policy_color(name: str) -> str:
    if name == "parliamentary_grpo":
        return "#E45756"
    if name == "parliamentary_base":
        return "#F58518"
    return "#4C78A8"


def _write_bar_chart(
    *,
    plt: Any,
    labels: list[str],
    values: list[float],
    title: str,
    ylabel: str,
    output_path: Path,
) -> Path:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.bar(labels, values, color="#4C78A8")
    axis.set_title(title)
    axis.set_xlabel("Policy baseline")
    axis.set_ylabel(ylabel)
    axis.tick_params(axis="x", labelrotation=25)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)
    return output_path
