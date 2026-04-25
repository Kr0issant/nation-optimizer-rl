"""Seeded in-process benchmark runner for rule-based policy adapters."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from agents.base import PolicyAdapter
from agents.rule_based import (
    ConservativeAdapter,
    EqualSplitAdapter,
    GreedyAdapter,
    OptimalZoneAdapter,
    RandomAdapter,
)
from core.config import GameConfig
from core.game import NationGame, PROPOSAL_STATUS_APPROVED
from schemas.actions import Action
from schemas.metrics import EpisodeMetrics
from schemas.observations import Observation, OwnDepartmentObservation, ProposalObservation, VoteObservation
from schemas.phases import Phase, valid_action_types_for_phase
from telemetry.metrics_collector import MetricsCollector
from telemetry.run_summary import RunSummary


DEFAULT_SEEDS = (1, 2, 3)
DEFAULT_MAX_ROUNDS = 3
DEFAULT_OUTPUT_PATH = Path("assets/results/benchmark_summary.json")

AdapterFactory = Callable[[int], PolicyAdapter]

BASELINE_FACTORIES: tuple[tuple[str, AdapterFactory], ...] = (
    ("random", lambda seed: RandomAdapter(seed=seed)),
    ("greedy", lambda seed: GreedyAdapter()),
    ("equal_split", lambda seed: EqualSplitAdapter()),
    ("conservative", lambda seed: ConservativeAdapter()),
    ("optimal_zone", lambda seed: OptimalZoneAdapter()),
)


def run_benchmarks(
    *,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    disable_events: bool = False,
) -> dict[str, Any]:
    seed_values = tuple(seeds)
    config = replace(GameConfig.from_json(), MAX_ROUNDS=max_rounds)
    policy_results = []

    for policy_name, adapter_factory in BASELINE_FACTORIES:
        episodes = tuple(
            run_episode(
                policy_name=policy_name,
                adapter=adapter_factory(seed),
                seed=seed,
                config=config,
                disable_events=disable_events,
            )
            for seed in seed_values
        )
        summary = RunSummary(run_id=policy_name, episodes=episodes)
        policy_results.append(
            {
                "policy": policy_name,
                "summary": summarize_run(summary),
                "episodes": [asdict(episode) for episode in episodes],
            }
        )

    return {
        "run_id": "rule_based_baselines",
        "seeds": list(seed_values),
        "max_rounds": max_rounds,
        "events": "disabled" if disable_events else "enabled",
        "policies": policy_results,
    }


def run_episode(
    *,
    policy_name: str,
    adapter: PolicyAdapter,
    seed: int,
    config: GameConfig,
    disable_events: bool = False,
) -> EpisodeMetrics:
    episode_id = f"{policy_name}-seed-{seed}"
    game = NationGame(config=config, seed=seed)
    if disable_events:
        game.event_engine._distribution = {"no_event": 1.0}
        game.reset()

    adapter.reset()
    collector = MetricsCollector()
    last_recorded_reward = 0.0
    step_count = 0
    max_phase_steps = max(config.MAX_ROUNDS * 100, 100)

    while not game.done:
        step_count += 1
        if step_count > max_phase_steps:
            raise RuntimeError(f"Benchmark episode did not terminate: {episode_id}")

        phase_before_step = game.phase
        actions = _actions_for_phase(game, adapter)
        result = game.step(actions)
        if phase_before_step is Phase.DEBATE and game.phase is Phase.DEBATE:
            game.force_advance_phase()

        _record_action_outcomes(collector, result.info)
        _record_phase_metrics(collector, game, phase_before_step)

        reward_delta = game.total_reward - last_recorded_reward
        if reward_delta:
            collector.record_reward(reward_delta, round_number=result.round_num)
            last_recorded_reward = game.total_reward

    final_prosperity = game.last_total_revenue / max(game.population.value, 1)
    collector.record_final_state(
        final_treasury=game.treasury.balance,
        final_prosperity=final_prosperity,
        final_productivity=game.productivity.value,
        termination_reason=game.termination_reason,
        rounds_survived=game.round,
    )
    return collector.build_summary(episode_id)


def summarize_run(summary: RunSummary) -> dict[str, Any]:
    return {
        "episode_count": summary.episode_count,
        "mean_episode_return": summary.mean_total_reward,
        "mean_survival_rounds": summary.mean_rounds_survived,
        "critical_failure_rate": summary.critical_failure_rate,
        "bankruptcy_rate": summary.bankruptcy_rate,
        "shutdown_rate": summary.shutdown_rate,
        "mean_final_prosperity": summary.mean_final_prosperity,
        "mean_average_revenue_factor": summary.mean_average_revenue_factor,
        "mean_treasury_stability": summary.mean_treasury_stability,
        "mean_productivity_growth": summary.mean_productivity_growth,
        "invalid_action_count": summary.invalid_action_count,
        "parse_error_count": summary.parse_error_count,
        "debate_message_count": summary.debate_message_count,
        "proposals_passed_count": summary.proposals_passed_count,
    }


def write_benchmark_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _actions_for_phase(game: NationGame, adapter: PolicyAdapter) -> list[dict[str, Any]]:
    valid_actions = valid_action_types_for_phase(game.phase)
    if not valid_actions:
        return []

    state = game.state()
    actions = []
    for agent_id in game.config.SECTOR_ORDER:
        observation = _observation_for_agent(state, agent_id)
        action = adapter.act(observation, valid_actions, agent_id)
        if action.type.value in valid_actions:
            actions.append(_action_to_game_dict(action, agent_id))
    return actions


def _observation_for_agent(state: dict[str, Any], agent_id: str) -> Observation:
    sector = state["sectors"][agent_id]
    return Observation(
        round=state["round"],
        phase=state["phase"],
        treasury=state["treasury"],
        own_department=OwnDepartmentObservation(
            name=agent_id,
            allocated_budget=sector.get("allocation"),
            consumption=sector.get("consumption"),
            surplus=sector.get("surplus"),
            efficiency_rating=sector.get("revenue_factor"),
            treasury_surplus_returned_this_round=state.get("last_total_surplus"),
        ),
        event_ledger=tuple(state["event_ledger"]),
        proposals=tuple(
            ProposalObservation(
                proposal_id=proposal["proposal_id"],
                department=proposal["department"],
                amount=proposal["amount"],
                status=proposal["status"],
                agent_id=proposal.get("agent_id"),
                votes=dict(proposal.get("votes", {})),
            )
            for proposal in state["proposals"]
        ),
        votes=tuple(
            VoteObservation(
                proposal_id=vote["proposal_id"],
                agent_id=vote["agent_id"],
                vote=vote["vote"],
            )
            for vote in state["votes"]
        ),
        debate_messages=tuple(state["debate_messages"]),
        termination=state["termination"],
    )


def _action_to_game_dict(action: Action, agent_id: str) -> dict[str, Any]:
    payload = action.to_dict()
    payload["agent_id"] = agent_id
    if "department" not in payload:
        payload["department"] = agent_id
    return payload


def _record_action_outcomes(collector: MetricsCollector, info: dict[str, Any]) -> None:
    for _accepted_action in info.get("accepted_actions", []):
        collector.record_action_validation(is_valid=True)
    for _rejected_action in info.get("rejected_actions", []):
        collector.record_action_validation(is_valid=False)
    for _ignored_action in info.get("ignored_actions", []):
        collector.record_action_validation(is_valid=False)


def _record_phase_metrics(
    collector: MetricsCollector,
    game: NationGame,
    phase_before_step: Phase,
) -> None:
    collector.record_round(game.round)
    collector.record_treasury(game.treasury.balance)
    collector.record_productivity(game.productivity.value)

    accepted_actions = game.last_info.get("accepted_actions", [])
    collector.record_debate_message(
        sum(1 for action in accepted_actions if action.get("type") == "DEBATE")
    )

    if phase_before_step is Phase.BUDGET_EXECUTION:
        collector.record_proposal_passed(
            sum(1 for proposal in game.proposals if proposal.status == PROPOSAL_STATUS_APPROVED)
        )

    if phase_before_step is Phase.REVENUE_CALCULATION:
        for sector in game.sectors.values():
            collector.record_revenue_factor(sector.revenue_factor_value)


def _parse_seeds(raw_seeds: list[str]) -> tuple[int, ...]:
    values: list[int] = []
    for raw_seed in raw_seeds:
        values.extend(int(value.strip()) for value in raw_seed.split(",") if value.strip())
    if not values:
        raise argparse.ArgumentTypeError("at least one seed is required")
    return tuple(values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        nargs="+",
        default=[",".join(str(seed) for seed in DEFAULT_SEEDS)],
        help="Shared random seeds, either space-separated or comma-separated.",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=DEFAULT_MAX_ROUNDS,
        help="Maximum rounds per episode.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="JSON summary path.",
    )
    parser.add_argument(
        "--disable-events",
        action="store_true",
        help="Force no-event rounds for deterministic tiny CI runs.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Also write benchmark plots under --plot-dir.",
    )
    parser.add_argument(
        "--plot-dir",
        type=Path,
        default=Path("assets/results"),
        help="Directory for generated PNG plots.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    payload = run_benchmarks(
        seeds=_parse_seeds(args.seeds),
        max_rounds=args.max_rounds,
        disable_events=args.disable_events,
    )
    write_benchmark_json(payload, args.output)
    if args.plot:
        from telemetry.plotter import plot_benchmark_payload

        plot_benchmark_payload(payload, args.plot_dir)
    print(json.dumps(payload["policies"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
