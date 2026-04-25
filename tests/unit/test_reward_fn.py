"""Unit tests for the GRPO reward function."""

from __future__ import annotations

import json
import math

import pytest

from training.reward_fn import (
    ABSTAIN_REWARD,
    ILLEGAL_ACTION_REWARD,
    PARSE_FAIL_REWARD,
    PROPOSE_BASE_REWARD,
    PROPOSE_FACTOR_WEIGHT,
    make_reward_fn,
)


SECTOR_HEALTH = {"critical": 36.0, "demand": 90.0, "surplus": 135.0}
SECTOR_DEFENSE = {"critical": 40.0, "demand": 100.0, "surplus": 150.0}
ALL_SECTORS = {"Health": SECTOR_HEALTH, "Defense": SECTOR_DEFENSE}


def _row(
    *,
    agent_id: str = "Health",
    valid_actions: tuple[str, ...] = ("PROPOSE_BUDGET", "ABSTAIN_FROM_PROPOSAL"),
    treasury: float = 1000.0,
    proposals: tuple[dict, ...] = (),
) -> dict:
    return {
        "agent_id": agent_id,
        "valid_actions": valid_actions,
        "treasury": treasury,
        "own_sector": {"name": agent_id, **ALL_SECTORS[agent_id]},
        "all_sectors": ALL_SECTORS,
        "proposals": list(proposals),
    }


def _score(completion: str, row: dict) -> float:
    reward = make_reward_fn()
    columns = {key: [value] for key, value in row.items()}
    return reward(prompts=["unused"], completions=[completion], **columns)[0]


def _propose(department: str, amount: float) -> str:
    return json.dumps(
        {
            "type": "PROPOSE_BUDGET",
            "department": department,
            "amount": amount,
            "justification": "test",
        }
    )


def test_malformed_json_returns_parse_failure_reward() -> None:
    assert _score("not json", _row()) == PARSE_FAIL_REWARD


def test_vote_in_proposal_phase_is_illegal() -> None:
    completion = json.dumps({"type": "VOTE", "proposal_id": "p-0", "vote": "YES"})
    assert _score(completion, _row()) == ILLEGAL_ACTION_REWARD


def test_propose_budget_in_profit_zone_is_high_positive() -> None:
    amount = SECTOR_HEALTH["demand"] * 1.3
    score = _score(_propose("Health", amount), _row())

    t = (amount - SECTOR_HEALTH["demand"]) / (SECTOR_HEALTH["surplus"] - SECTOR_HEALTH["demand"])
    rf = 1.0 + (1.8 - 1.0) * t
    expected = PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (rf - 1.0)
    assert math.isclose(score, expected, rel_tol=1e-6)
    assert score > 0.6


def test_propose_budget_below_critical_is_strongly_negative() -> None:
    amount = SECTOR_HEALTH["critical"] * 0.5
    score = _score(_propose("Health", amount), _row())
    expected = PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (0.0 - 1.0)
    assert math.isclose(score, expected, rel_tol=1e-6)
    assert score < 0.0


def test_propose_budget_for_wrong_department_is_illegal() -> None:
    completion = _propose("Defense", SECTOR_DEFENSE["demand"])
    assert _score(completion, _row(agent_id="Health")) == ILLEGAL_ACTION_REWARD


def test_propose_budget_above_treasury_is_illegal() -> None:
    completion = _propose("Health", 5_000.0)
    assert _score(completion, _row(treasury=1_000.0)) == ILLEGAL_ACTION_REWARD


def test_propose_budget_negative_amount_is_illegal() -> None:
    completion = _propose("Health", -10.0)
    assert _score(completion, _row()) == ILLEGAL_ACTION_REWARD


def test_vote_yes_on_profit_zone_proposal_is_positive() -> None:
    proposal = {
        "proposal_id": "p-1",
        "department": "Defense",
        "amount": SECTOR_DEFENSE["demand"] * 1.3,
    }
    completion = json.dumps({"type": "VOTE", "proposal_id": "p-1", "vote": "YES"})
    row = _row(
        agent_id="Health",
        valid_actions=("VOTE",),
        proposals=(proposal,),
    )
    assert _score(completion, row) > 0.0


def test_vote_yes_on_critical_failure_proposal_is_negative() -> None:
    proposal = {
        "proposal_id": "p-1",
        "department": "Defense",
        "amount": SECTOR_DEFENSE["critical"] * 0.5,
    }
    completion = json.dumps({"type": "VOTE", "proposal_id": "p-1", "vote": "YES"})
    row = _row(
        agent_id="Health",
        valid_actions=("VOTE",),
        proposals=(proposal,),
    )
    score = _score(completion, row)
    assert score == pytest.approx(-1.0)


def test_vote_no_on_critical_failure_proposal_is_positive() -> None:
    proposal = {
        "proposal_id": "p-1",
        "department": "Defense",
        "amount": SECTOR_DEFENSE["critical"] * 0.5,
    }
    completion = json.dumps({"type": "VOTE", "proposal_id": "p-1", "vote": "NO"})
    row = _row(
        agent_id="Health",
        valid_actions=("VOTE",),
        proposals=(proposal,),
    )
    score = _score(completion, row)
    assert score == pytest.approx(1.0)


def test_vote_abstain_choice_is_zero() -> None:
    proposal = {
        "proposal_id": "p-1",
        "department": "Defense",
        "amount": SECTOR_DEFENSE["demand"] * 1.3,
    }
    completion = json.dumps({"type": "VOTE", "proposal_id": "p-1", "vote": "ABSTAIN"})
    row = _row(
        agent_id="Health",
        valid_actions=("VOTE",),
        proposals=(proposal,),
    )
    assert _score(completion, row) == ABSTAIN_REWARD


def test_vote_for_unknown_proposal_is_illegal() -> None:
    completion = json.dumps({"type": "VOTE", "proposal_id": "p-missing", "vote": "YES"})
    row = _row(agent_id="Health", valid_actions=("VOTE",))
    assert _score(completion, row) == ILLEGAL_ACTION_REWARD


def test_abstain_from_proposal_is_zero() -> None:
    completion = json.dumps({"type": "ABSTAIN_FROM_PROPOSAL"})
    assert _score(completion, _row()) == ABSTAIN_REWARD


def test_reward_function_handles_full_grpo_batch() -> None:
    reward = make_reward_fn()
    rows = [
        _row(agent_id="Health"),
        _row(agent_id="Defense"),
    ]
    completions = [
        _propose("Health", SECTOR_HEALTH["demand"] * 1.3),
        _propose("Defense", SECTOR_DEFENSE["demand"] * 1.3),
    ]
    columns: dict[str, list] = {}
    for row in rows:
        for key, value in row.items():
            columns.setdefault(key, []).append(value)

    scores = reward(
        prompts=["p1", "p2"],
        completions=completions,
        **columns,
    )
    assert len(scores) == 2
    assert all(score > 0.6 for score in scores)


def test_reward_function_handles_chat_style_completion_payloads() -> None:
    completion = [{"role": "assistant", "content": _propose("Health", SECTOR_HEALTH["demand"])}]
    reward = make_reward_fn()
    columns = {key: [value] for key, value in _row().items()}
    scores = reward(prompts=["p"], completions=[completion], **columns)
    assert math.isclose(scores[0], PROPOSE_BASE_REWARD, rel_tol=1e-6)
