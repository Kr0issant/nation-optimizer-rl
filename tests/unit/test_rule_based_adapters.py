from agents.rule_based import ConservativeAdapter, EqualSplitAdapter, GreedyAdapter, RandomAdapter
from schemas.actions import ActionType, VoteChoice
from schemas.observations import Observation, OwnDepartmentObservation, ProposalObservation
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


def test_random_adapter_samples_legal_proposal_amount() -> None:
    observation = _proposal_observation(treasury=900.0, department="Health")
    action = RandomAdapter(seed=123).act(
        observation=observation,
        valid_actions={"PROPOSE_BUDGET"},
        agent_id="Health",
    )

    assert action.type is ActionType.PROPOSE_BUDGET
    assert action.department == "Health"
    assert 0.0 <= action.amount <= 900.0


def test_random_adapter_votes_only_on_other_departments_proposals() -> None:
    observation = Observation(
        round=1,
        phase=Phase.VOTING,
        treasury=900.0,
        own_department=OwnDepartmentObservation(name="Health"),
        proposals=(
            ProposalObservation(proposal_id="own", department="Health", amount=90.0),
            ProposalObservation(proposal_id="other", department="Defense", amount=100.0),
        ),
    )

    action = RandomAdapter(seed=1).act(
        observation=observation,
        valid_actions={"VOTE"},
        agent_id="Health",
    )

    assert action.type is ActionType.VOTE
    assert action.proposal_id == "other"
    assert action.vote in set(VoteChoice)


def test_random_adapter_vote_candidates_keep_each_proposal_id() -> None:
    observation = Observation(
        round=1,
        phase=Phase.VOTING,
        treasury=900.0,
        own_department=OwnDepartmentObservation(name="Health"),
        proposals=(
            ProposalObservation(proposal_id="defense", department="Defense", amount=100.0),
            ProposalObservation(proposal_id="education", department="Education", amount=120.0),
        ),
    )

    candidates = RandomAdapter(seed=1)._candidate_actions(
        observation=observation,
        valid_actions={"VOTE"},
        agent_id="Health",
    )

    proposal_ids = {candidate().proposal_id for candidate in candidates}
    assert proposal_ids == {"defense", "education"}


def test_rule_based_adapters_vote_on_other_pending_proposal() -> None:
    observation = Observation(
        round=1,
        phase=Phase.VOTING,
        treasury=900.0,
        own_department=OwnDepartmentObservation(name="Health"),
        proposals=(
            ProposalObservation(proposal_id="own", department="Health", amount=90.0),
            ProposalObservation(proposal_id="other", department="Defense", amount=100.0),
        ),
    )

    for adapter in (GreedyAdapter(), EqualSplitAdapter(), ConservativeAdapter()):
        action = adapter.act(
            observation=observation,
            valid_actions={"VOTE"},
            agent_id="Health",
        )

        assert action.type is ActionType.VOTE
        assert action.proposal_id == "other"


def _proposal_observation(treasury: float, department: str) -> Observation:
    return Observation(
        round=1,
        phase=Phase.PROPOSAL,
        treasury=treasury,
        own_department=OwnDepartmentObservation(name=department),
    )
