import json

import pytest
from pydantic import ValidationError

from server.environment import NationEnvironment
from server.models import ParliamentaryAction, ParliamentaryObservation


def make_debate_action(agent_id: str = "Social") -> ParliamentaryAction:
    return ParliamentaryAction(agent_id=agent_id, type="DEBATE", message="")


def assert_state_contract(state: ParliamentaryObservation) -> None:
    dumped_state = state.model_dump()

    assert isinstance(state, ParliamentaryObservation)
    assert "treasury" in dumped_state
    assert "population" in dumped_state
    assert "productivity" in dumped_state
    assert "event_ledger" in dumped_state


def assert_state_is_serializable(state: ParliamentaryObservation) -> None:
    serialized = state.model_dump_json()

    assert json.loads(serialized) == state.model_dump(mode="json")


def test_reset_returns_state_and_info_dict():
    env = NationEnvironment(seed=123)

    state, info = env.reset()

    assert_state_contract(state)
    assert_state_is_serializable(state)
    assert info == {}


def test_step_returns_openenv_tuple_and_info_contract():
    env = NationEnvironment(seed=123)
    env.reset()

    state, reward, terminated, truncated, info = env.step(make_debate_action())

    assert_state_contract(state)
    assert_state_is_serializable(state)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_invalid_action_amount_type_fails_validation():
    with pytest.raises(ValidationError):
        ParliamentaryAction(
            agent_id="Social",
            type="PROPOSE_BUDGET",
            department="Social",
            amount="not_a_number",
            justification="test",
        )


def test_one_random_valid_action_does_not_crash():
    env = NationEnvironment(seed=123)
    env.reset()
    action = ParliamentaryAction(
        agent_id="Social",
        type="PROPOSE_BUDGET",
        department="Social",
        amount=10.0,
        justification="test",
    )

    state, reward, terminated, truncated, info = env.step(action)

    assert_state_contract(state)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "termination_reason" in info


def test_repeated_stepping_does_not_crash():
    env = NationEnvironment(seed=123)
    env.reset()

    for _ in range(20):
        state, _, terminated, truncated, info = env.step(make_debate_action())

        assert_state_contract(state)
        assert truncated is False
        assert isinstance(info, dict)
        if terminated:
            break
