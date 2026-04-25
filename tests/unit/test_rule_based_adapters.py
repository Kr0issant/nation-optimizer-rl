from agents.rule_based import EqualSplitAdapter, GreedyAdapter
from schemas.actions import ActionType
from schemas.observations import Observation, OwnDepartmentObservation
from schemas.phases import Phase


def test_greedy_adapter_requests_visible_treasury_for_own_department() -> None:
    observation = _proposal_observation(treasury=900.0, department="Defense")
    action = GreedyAdapter().act(
        observation=observation,
        valid_actions={"PROPOSE_BUDGET"},
        agent_id="Defense",
    )

    assert action.type is ActionType.PROPOSE_BUDGET
    assert action.department == "Defense"
    assert action.amount == 900.0


def test_equal_split_adapter_requests_one_department_share() -> None:
    observation = _proposal_observation(treasury=900.0, department="Health")
    action = EqualSplitAdapter(department_count=6).act(
        observation=observation,
        valid_actions={"PROPOSE_BUDGET"},
        agent_id="Health",
    )

    assert action.type is ActionType.PROPOSE_BUDGET
    assert action.department == "Health"
    assert action.amount == 150.0


def _proposal_observation(treasury: float, department: str) -> Observation:
    return Observation(
        round=1,
        phase=Phase.PROPOSAL,
        treasury=treasury,
        own_department=OwnDepartmentObservation(name=department),
    )
