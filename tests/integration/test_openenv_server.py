import json

from server.environment import NationOpenEnv
from server.models import NationAction, NationObservation, NationState


def assert_json_serializable(value: object) -> None:
    json.dumps(value)


def test_openenv_wrapper_resets_steps_and_serializes_state() -> None:
    env = NationOpenEnv()

    reset_observation = env.reset(seed=123, episode_id="integration-smoke")
    phase_2 = env.step(NationAction(actions=[]))
    debate = env.step(
        NationAction(
            actions={
                "type": "DEBATE",
                "agent_id": "Health",
                "message": "Health expects demand pressure this quarter.",
            }
        )
    )

    assert isinstance(reset_observation, NationObservation)
    assert isinstance(env.state, NationState)
    assert phase_2.state["phase"] == 2
    assert debate.info["accepted_actions"][0]["type"] == "DEBATE"
    assert not debate.done

    assert_json_serializable(reset_observation.model_dump(mode="json"))
    assert_json_serializable(debate.model_dump(mode="json"))
    assert_json_serializable(env.state.model_dump(mode="json"))


def test_openenv_wrapper_supports_direct_allocation_smoke_round() -> None:
    env = NationOpenEnv()
    observation = env.reset(seed=7)
    allocations = {
        department: sector["demand"] * 1.1
        for department, sector in observation.state["sectors"].items()
    }

    result = env.step(NationAction(direct_allocations=allocations))

    assert result.state["round"] == 1
    assert result.state["last_total_allocation"] > 0
    assert result.reward is not None
    assert_json_serializable(result.model_dump(mode="json"))
