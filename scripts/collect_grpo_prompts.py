"""Collect prompts for GRPO training from rule-based rollouts.

Runs the :class:`OptimalZoneAdapter` baseline for ``--seeds`` episodes and, for
every Phase 3 (``PROPOSAL``) and Phase 4 (``VOTING``) minister turn, writes one
JSONL record with everything the reward function needs:

- ``prompt``: literal output of :func:`render_minister_prompt` so the dataset
  stays in lockstep with the inference template.
- ``agent_id`` and ``valid_actions``: who is acting and what action types are
  legal in this phase.
- ``treasury``, ``own_sector`` (critical/demand/surplus), ``proposals`` and
  ``all_sectors``: public state needed by the reward function to score
  ``PROPOSE_BUDGET`` / ``VOTE`` completions against the same
  piecewise revenue math the engine uses.

Phase 2 (``DEBATE``) prompts are deliberately excluded — debate is inference
only and never receives reward updates.

Example
-------

::

    python -m scripts.collect_grpo_prompts \
        --seeds 50 --max-rounds 12 \
        --output assets/datasets/grpo_prompts.jsonl

    # Optionally push the same JSONL as a private HF dataset:
    python -m scripts.collect_grpo_prompts \
        --seeds 50 --max-rounds 12 \
        --push-to-hub <user>/nation-parliamentary-prompts
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from agents.rule_based import OptimalZoneAdapter
from core.config import GameConfig
from core.game import NationGame
from evaluation.benchmark_policies import (
    _action_to_game_dict,
    _observation_for_agent,
)
from llm_integration.context_builder import build_sector_thresholds
from llm_integration.prompts.minister import render_minister_prompt
from schemas.phases import Phase, valid_action_types_for_phase

DEFAULT_OUTPUT_PATH = Path("assets/datasets/grpo_prompts.jsonl")
TRAINING_PHASES: frozenset[Phase] = frozenset({Phase.PROPOSAL, Phase.VOTING})


def collect_records(
    *,
    seeds: Iterable[int],
    max_rounds: int,
    disable_events: bool = False,
) -> list[dict[str, Any]]:
    """Roll out the optimal-zone baseline and snapshot Phase 3/4 prompts.

    Returns a list of JSON-serialisable records, one per (seed, round, phase,
    agent) tuple where ``phase`` is ``PROPOSAL`` or ``VOTING``.
    """
    config = replace(GameConfig.from_json(), MAX_ROUNDS=max_rounds)
    records: list[dict[str, Any]] = []

    for seed in seeds:
        game = NationGame(config=config, seed=seed)
        if disable_events:
            game.event_engine._distribution = {"no_event": 1.0}
            game.reset(seed=seed)

        adapter = OptimalZoneAdapter()
        adapter.reset()
        records.extend(_collect_episode(game=game, adapter=adapter, seed=seed))

    return records


def _collect_episode(
    *,
    game: NationGame,
    adapter: OptimalZoneAdapter,
    seed: int,
) -> list[dict[str, Any]]:
    episode_records: list[dict[str, Any]] = []
    max_phase_steps = max(game.config.MAX_ROUNDS * 100, 100)
    step_count = 0

    while not game.done:
        step_count += 1
        if step_count > max_phase_steps:
            raise RuntimeError(
                f"Prompt collection did not terminate for seed={seed}."
            )

        phase_before = game.phase
        valid_actions = valid_action_types_for_phase(phase_before)
        state_before = game.state()
        actions: list[dict[str, Any]] = []

        for agent_id in game.config.SECTOR_ORDER:
            observation = _observation_for_agent(state_before, agent_id)

            if (
                phase_before in TRAINING_PHASES
                and valid_actions
                and observation.own_department is not None
            ):
                episode_records.append(
                    _make_record(
                        observation=observation,
                        state=state_before,
                        agent_id=agent_id,
                        valid_actions=valid_actions,
                        seed=seed,
                    )
                )

            if not valid_actions:
                continue
            action = adapter.act(observation, valid_actions, agent_id)
            if action.type.value in valid_actions:
                actions.append(_action_to_game_dict(action, agent_id))

        game.step(actions)
        if phase_before is Phase.DEBATE and game.phase is Phase.DEBATE:
            game.force_advance_phase()

    return episode_records


def _make_record(
    *,
    observation: Any,
    state: dict[str, Any],
    agent_id: str,
    valid_actions: Iterable[str],
    seed: int,
) -> dict[str, Any]:
    valid_action_set = set(valid_actions)
    prompt = render_minister_prompt(observation, agent_id, valid_action_set)
    sectors = build_sector_thresholds(state)
    own_sector = sectors[agent_id]
    proposals = [
        {
            "proposal_id": str(proposal["proposal_id"]),
            "department": str(proposal["department"]),
            "amount": float(proposal["amount"]),
            "status": str(proposal.get("status", "pending")),
            "agent_id": proposal.get("agent_id"),
        }
        for proposal in state.get("proposals", [])
    ]
    return {
        "prompt": prompt,
        "agent_id": agent_id,
        "valid_actions": sorted(valid_action_set),
        "phase": Phase(state["phase"]).name,
        "round": int(state["round"]),
        "max_rounds": int(state.get("max_rounds", 0) or 0),
        "treasury": float(state["treasury"]),
        "total_critical": float(state.get("total_critical", 0.0) or 0.0),
        "own_sector": {"name": agent_id, **own_sector},
        "proposals": proposals,
        "all_sectors": sectors,
        "seed": int(seed),
    }


def write_jsonl(records: Iterable[dict[str, Any]], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def push_to_hub(
    output_path: Path,
    repo_id: str,
    *,
    private: bool,
) -> None:
    """Upload the collected JSONL as a private HF dataset.

    Importing :mod:`datasets` is deferred so the collector remains importable
    in environments (CI, local CPU dev) that do not have the optional training
    extras installed.
    """
    from datasets import load_dataset

    dataset = load_dataset("json", data_files=str(output_path), split="train")
    dataset.push_to_hub(repo_id, private=private)


def _parse_seed_count(value: str) -> int:
    try:
        seeds = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--seeds must be an integer: {value!r}") from exc
    if seeds <= 0:
        raise argparse.ArgumentTypeError("--seeds must be a positive integer.")
    return seeds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=_parse_seed_count,
        default=50,
        help="Number of seeded episodes to roll out (uses seeds 0..N-1).",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=12,
        help="MAX_ROUNDS override per episode.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="JSONL output path.",
    )
    parser.add_argument(
        "--disable-events",
        action="store_true",
        help="Force no-event rounds for tiny deterministic dev runs.",
    )
    parser.add_argument(
        "--push-to-hub",
        type=str,
        default=None,
        help="Optional HF dataset repo id to push the JSONL to.",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="When pushing, publish as a public dataset (default: private).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    seed_values = tuple(range(args.seeds))
    records = collect_records(
        seeds=seed_values,
        max_rounds=args.max_rounds,
        disable_events=args.disable_events,
    )
    written = write_jsonl(records, args.output)
    print(f"Wrote {written} prompt records to {args.output}")
    if args.push_to_hub:
        push_to_hub(args.output, args.push_to_hub, private=not args.public)
        print(f"Pushed dataset to https://huggingface.co/datasets/{args.push_to_hub}")


if __name__ == "__main__":
    main()
