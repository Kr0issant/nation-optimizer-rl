import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.events import Event
from core.game import NationGame
from schemas.actions import ActionType, VoteChoice
from schemas.phases import Phase
from server.app import app
from server.environment import NationEnvironment
from server.models import ParliamentaryAction, ParliamentaryObservation

DEPARTMENTS = ("Social", "Agriculture", "Health", "Education", "Defense", "Commerce")


def make_debate_action(agent_id: str = "Social") -> ParliamentaryAction:
    return ParliamentaryAction(agent_id=agent_id, type="DEBATE", message="")


def assert_state_contract(state: ParliamentaryObservation) -> None:
    dumped_state = state.model_dump()

    assert isinstance(state, ParliamentaryObservation)
    assert "treasury" in dumped_state
    assert "population" in dumped_state
    assert "productivity" in dumped_state
    assert "event_ledger" in dumped_state
    assert "year" in dumped_state
    assert "quarter" in dumped_state


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
    assert isinstance(info, dict)


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


def test_event_affected_sectors_are_exposed_as_affected_departments():
    env = NationEnvironment(seed=123)
    env.reset()
    env.game.current_events = [
        Event(
            id="e-test",
            name="Hospital Surge",
            severity=3,
            affected_sectors={"Health": 1.5, "Commerce": 1.1},
            category="crisis",
            narrative="Hospitals and trade routes are under pressure.",
        )
    ]

    state = env._build_observation(agent_id="Health")

    assert state.current_events[0].affected_departments == ["Health", "Commerce"]


def test_abstaining_departments_do_not_trigger_critical_failure_on_execution():
    game = NationGame(seed=123)
    game.event_engine._distribution = {"no_event": 1.0}
    game.reset()

    game.step()
    game.force_advance_phase()

    game.step(
        [
            {
                "type": ActionType.PROPOSE_BUDGET,
                "agent_id": "Health",
                "department": "Health",
                "amount": game.config.SECTOR_BASELINES["Health"],
                "justification": "Fund expected demand",
            },
            *[
                {
                    "type": ActionType.ABSTAIN_FROM_PROPOSAL,
                    "agent_id": department,
                    "department": department,
                }
                for department in DEPARTMENTS
                if department != "Health"
            ],
        ]
    )

    health_proposal = game.proposals[0]
    game.step(
        [
            {
                "type": ActionType.VOTE,
                "agent_id": department,
                "proposal_id": health_proposal.proposal_id,
                "vote": VoteChoice.YES,
            }
            for department in DEPARTMENTS
            if department != "Health"
        ]
    )
    result = game.step()

    assert not result.done
    assert result.termination_reason is None
    assert health_proposal.status == "approved"


def test_fastapi_openenv_endpoints_reset_and_step():
    client = TestClient(app)

    reset_response = client.post("/reset", json={"seed": 123})
    assert reset_response.status_code == 200
    assert reset_response.json()["observation"]["round"] == 1

    step_response = client.post(
        "/step",
        json={
            "action": {
                "agent_id": "Social",
                "type": "DEBATE",
                "message": "Social services are ready to coordinate.",
            }
        },
    )

    assert step_response.status_code == 200
    assert step_response.json()["done"] is False
