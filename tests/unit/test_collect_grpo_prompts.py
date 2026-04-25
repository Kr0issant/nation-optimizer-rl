"""Unit tests for the GRPO prompt collector."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_integration.context_builder import HIDDEN_EVENT_FIELDS, build_sector_thresholds
from llm_integration.prompts.minister import render_minister_prompt
from scripts.collect_grpo_prompts import (
    TRAINING_PHASES,
    collect_records,
    write_jsonl,
)
from schemas.observations import (
    Observation,
    OwnDepartmentObservation,
    ProposalObservation,
)
from schemas.phases import Phase


def test_collected_records_only_cover_proposal_and_voting_phases() -> None:
    records = collect_records(seeds=(0,), max_rounds=2, disable_events=True)

    assert records, "expected at least one collected record"
    phases = {record["phase"] for record in records}
    assert phases <= {Phase.PROPOSAL.name, Phase.VOTING.name}
    assert "DEBATE" not in phases
    assert all(Phase[record["phase"]] in TRAINING_PHASES for record in records)


def test_records_carry_public_state_for_reward_function() -> None:
    records = collect_records(seeds=(0,), max_rounds=1, disable_events=True)

    proposal_records = [r for r in records if r["phase"] == Phase.PROPOSAL.name]
    assert proposal_records, "no PROPOSAL records collected"
    proposal = proposal_records[0]

    assert proposal["agent_id"] in proposal["all_sectors"]
    own_sector = proposal["own_sector"]
    assert own_sector["name"] == proposal["agent_id"]
    for field in ("critical", "demand", "surplus"):
        assert field in own_sector
        assert isinstance(own_sector[field], float)
    assert proposal["treasury"] > 0
    assert isinstance(proposal["proposals"], list)
    assert sorted(proposal["valid_actions"]) == sorted(proposal["valid_actions"])


def test_collected_prompt_matches_render_minister_prompt_exactly() -> None:
    """The collector must use the live template; this guards against drift."""
    observation = Observation(
        round=1,
        phase=Phase.PROPOSAL,
        treasury=1500.0,
        own_department=OwnDepartmentObservation(name="Health"),
        proposals=(
            ProposalObservation(
                proposal_id="p-1",
                department="Defense",
                amount=120.0,
                status="pending",
                agent_id="Defense",
                votes={},
            ),
        ),
    )
    valid_actions = {"PROPOSE_BUDGET", "ABSTAIN_FROM_PROPOSAL"}
    expected_prompt = render_minister_prompt(observation, "Health", valid_actions)

    assert "Minister for the 'Health' department" in expected_prompt
    assert "PROPOSE_BUDGET" in expected_prompt
    assert expected_prompt.startswith("You are the Minister")


def test_no_hidden_event_cost_fields_leak_into_prompts() -> None:
    records = collect_records(seeds=(0,), max_rounds=2, disable_events=False)
    assert records, "expected at least one record from a normal-event run"
    for record in records:
        prompt = record["prompt"]
        for hidden_field in HIDDEN_EVENT_FIELDS:
            assert f'"{hidden_field}"' not in prompt, (
                f"hidden field {hidden_field!r} leaked into a training prompt"
            )


def test_build_sector_thresholds_returns_public_fields_only() -> None:
    state = {
        "sectors": {
            "Health": {
                "critical": 36.8,
                "demand": 92.0,
                "surplus": 138.0,
                "wastage": 184.0,
                "allocation": 0.0,
            }
        }
    }
    thresholds = build_sector_thresholds(state)
    assert thresholds == {"Health": {"critical": 36.8, "demand": 92.0, "surplus": 138.0}}


def test_write_jsonl_is_round_trippable(tmp_path: Path) -> None:
    records = collect_records(seeds=(0,), max_rounds=1, disable_events=True)
    output = tmp_path / "prompts.jsonl"
    written = write_jsonl(records, output)
    assert written == len(records)

    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(records)
    for line in lines:
        parsed = json.loads(line)
        assert set(parsed) >= {"prompt", "agent_id", "valid_actions", "phase", "treasury"}


def test_seeds_argument_validation_rejects_non_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.collect_grpo_prompts import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--seeds", "0"])
