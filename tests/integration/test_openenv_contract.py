import json

import pytest
from pydantic import ValidationError

from server.environment import NationEnvironment
from server.models import NationAction, NationState


VALID_BID_COUNT = 6


def make_equal_bid_action() -> NationAction:
    return NationAction(bids=[0.0] * VALID_BID_COUNT)


def assert_state_contract(state: NationState) -> None:
    dumped_state = state.model_dump()

    assert isinstance(state, NationState)
    assert "treasury" in dumped_state
    assert "population" in dumped_state
    assert "productivity" in dumped_state
    assert "active_events" in dumped_state


def assert_state_is_serializable(state: NationState) -> None:
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

    state, reward, terminated, truncated, info = env.step(make_equal_bid_action())

    assert_state_contract(state)
    assert_state_is_serializable(state)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info["reward_breakdown"], dict)
    assert "termination_reason" in info


def test_invalid_action_length_fails_validation():
    with pytest.raises(ValidationError):
        NationAction(bids=[0.0] * (VALID_BID_COUNT - 1))


def test_one_random_valid_action_does_not_crash():
    env = NationEnvironment(seed=123)
    env.reset()
    action = NationAction(bids=[0.15, -0.4, 1.2, 0.0, 2.4, -1.1])

    state, reward, terminated, truncated, info = env.step(action)

    assert_state_contract(state)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info["reward_breakdown"], dict)
    assert "termination_reason" in info


def test_repeated_stepping_eventually_terminates_or_reaches_max_rounds():
    env = NationEnvironment(seed=123)
    env.reset()
    max_rounds = env.game.config.MAX_ROUNDS
    terminated = False

    for _ in range(max_rounds):
        state, _, terminated, truncated, info = env.step(make_equal_bid_action())

        assert_state_contract(state)
        assert truncated is False
        assert isinstance(info["reward_breakdown"], dict)
        assert "termination_reason" in info
        if terminated:
            break

    assert terminated or env.game.round >= max_rounds
