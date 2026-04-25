import math

import pytest

from core.parliament import ParliamentRoundState, Proposal, ProposalAbstention, VoteRecord
from schemas.actions import ActionType, VoteChoice
from schemas.phases import Phase


AGENT_DEPARTMENTS = {
    "social-minister": "Social",
    "agriculture-minister": "Agriculture",
    "health-minister": "Health",
}


def make_state(treasury: float = 100.0) -> ParliamentRoundState:
    return ParliamentRoundState(
        round_number=1,
        treasury_at_start=treasury,
        agent_departments=AGENT_DEPARTMENTS,
    )


def test_valid_proposal_accepted():
    state = make_state()

    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=40.0,
        justification="Keep essential services running",
    )

    assert proposal is not None
    assert proposal.department == "Social"
    assert proposal.amount == 40.0
    assert state.proposals == [proposal]


def test_wrong_department_rejected():
    state = make_state()

    with pytest.raises(ValueError, match="wrong_department"):
        state.submit_proposal(
            agent_id="social-minister",
            department="Health",
            amount=40.0,
            justification="Invalid portfolio",
        )


def test_negative_amount_rejected():
    state = make_state()

    with pytest.raises(ValueError, match="invalid_amount"):
        state.submit_proposal(
            agent_id="social-minister",
            department="Social",
            amount=-1.0,
            justification="Negative budget",
        )


@pytest.mark.parametrize("amount", [math.nan, math.inf, -math.inf, True])
def test_non_finite_and_bool_amounts_rejected(amount):
    state = make_state()

    with pytest.raises(ValueError, match="invalid_amount"):
        state.submit_proposal(
            agent_id="social-minister",
            department="Social",
            amount=amount,
            justification="Invalid amount",
        )


def test_amount_over_treasury_rejected():
    state = make_state(treasury=25.0)

    with pytest.raises(ValueError, match="exceeds_treasury"):
        state.submit_proposal(
            agent_id="social-minister",
            department="Social",
            amount=30.0,
            justification="Too expensive",
        )


def test_duplicate_proposal_rejected_after_first_valid_submission():
    state = make_state()
    state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="First proposal",
    )

    with pytest.raises(ValueError, match="duplicate_proposal"):
        state.submit_proposal(
            agent_id="social-minister",
            department="Social",
            amount=20.0,
            justification="Second proposal",
        )


def test_self_vote_rejected():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Self vote target",
    )

    with pytest.raises(ValueError, match="self_vote"):
        state.submit_vote(
            agent_id="social-minister",
            proposal_id=proposal.proposal_id,
            vote=VoteChoice.YES,
        )


def test_duplicate_vote_rejected():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Vote target",
    )
    state.submit_vote(
        agent_id="health-minister",
        proposal_id=proposal.proposal_id,
        vote=VoteChoice.YES,
    )

    with pytest.raises(ValueError, match="duplicate_vote"):
        state.submit_vote(
            agent_id="health-minister",
            proposal_id=proposal.proposal_id,
            vote=VoteChoice.NO,
        )


def test_unknown_voter_rejected():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Vote target",
    )

    with pytest.raises(ValueError, match="unknown_agent"):
        state.submit_vote(
            agent_id="unknown-minister",
            proposal_id=proposal.proposal_id,
            vote=VoteChoice.YES,
        )


def test_invalid_vote_value_rejected():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Vote target",
    )

    with pytest.raises(ValueError, match="invalid_vote"):
        state.submit_vote(
            agent_id="health-minister",
            proposal_id=proposal.proposal_id,
            vote="MAYBE",
        )


def test_yes_majority_approves():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Majority target",
    )
    state.submit_vote("agriculture-minister", proposal.proposal_id, VoteChoice.YES)
    state.submit_vote("health-minister", proposal.proposal_id, VoteChoice.YES)

    result = state.resolve()

    assert result.allocations["Social"] == 10.0
    assert result.approved_proposal_ids == [proposal.proposal_id]
    assert result.proposal_outcomes[proposal.proposal_id] == "approved"


def test_tie_rejects():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Tie target",
    )
    state.submit_vote("agriculture-minister", proposal.proposal_id, VoteChoice.YES)
    state.submit_vote("health-minister", proposal.proposal_id, VoteChoice.NO)

    result = state.resolve()

    assert result.allocations["Social"] == 0.0
    assert result.proposal_outcomes[proposal.proposal_id] == "rejected_tie"


def test_exact_fifty_percent_yes_boundary_rejects():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Boundary target",
    )
    state.submit_vote("agriculture-minister", proposal.proposal_id, VoteChoice.YES)
    state.submit_vote("health-minister", proposal.proposal_id, VoteChoice.NO)

    result = state.resolve()

    assert result.allocations["Social"] == 0.0
    assert result.proposal_outcomes[proposal.proposal_id] == "rejected_tie"


def test_all_abstain_rejects():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Abstain target",
    )
    state.submit_vote("agriculture-minister", proposal.proposal_id, VoteChoice.ABSTAIN)
    state.submit_vote("health-minister", proposal.proposal_id, VoteChoice.ABSTAIN)

    result = state.resolve()

    assert result.allocations["Social"] == 0.0
    assert result.proposal_outcomes[proposal.proposal_id] == "rejected_all_abstain"


def test_zero_vote_proposal_rejects_as_all_abstain():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="No vote target",
    )

    result = state.resolve()

    assert result.allocations["Social"] == 0.0
    assert result.proposal_outcomes[proposal.proposal_id] == "rejected_all_abstain"


def test_abstentions_excluded_from_majority():
    state = ParliamentRoundState(
        round_number=1,
        treasury_at_start=100.0,
        agent_departments={
            **AGENT_DEPARTMENTS,
            "education-minister": "Education",
        },
    )
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=10.0,
        justification="Abstention target",
    )
    state.submit_vote("agriculture-minister", proposal.proposal_id, VoteChoice.YES)
    state.submit_vote("health-minister", proposal.proposal_id, VoteChoice.ABSTAIN)
    state.submit_vote("education-minister", proposal.proposal_id, VoteChoice.ABSTAIN)

    result = state.resolve()

    assert result.allocations["Social"] == 10.0
    assert result.vote_counts[proposal.proposal_id] == {"YES": 1, "NO": 0, "ABSTAIN": 2}


def test_sequential_treasury_depletion_rejects_later_over_budget_proposal():
    state = make_state(treasury=50.0)
    first = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=40.0,
        justification="First in order",
    )
    second = state.submit_proposal(
        agent_id="health-minister",
        department="Health",
        amount=30.0,
        justification="Later in order",
    )

    state.submit_vote("agriculture-minister", first.proposal_id, VoteChoice.YES)
    state.submit_vote("health-minister", first.proposal_id, VoteChoice.YES)
    state.submit_vote("social-minister", second.proposal_id, VoteChoice.YES)
    state.submit_vote("agriculture-minister", second.proposal_id, VoteChoice.YES)

    result = state.resolve()

    assert result.allocations == {"Social": 40.0, "Agriculture": 0.0, "Health": 0.0}
    assert result.proposal_outcomes[first.proposal_id] == "approved"
    assert result.proposal_outcomes[second.proposal_id] == "rejected_exceeds_remaining_treasury"
    assert result.remaining_treasury == 10.0


def test_resolution_produces_allocation_dict_for_core_game():
    state = make_state()
    proposal = state.submit_proposal(
        agent_id="social-minister",
        department="Social",
        amount=25.0,
        justification="Core allocation",
    )
    state.submit_vote("agriculture-minister", proposal.proposal_id, VoteChoice.YES)
    state.submit_vote("health-minister", proposal.proposal_id, VoteChoice.YES)

    result = state.resolve()

    assert isinstance(result.allocations, dict)
    assert result.allocations == {"Social": 25.0, "Agriculture": 0.0, "Health": 0.0}


def test_collect_actions_over_phases_and_resolve_to_allocations():
    state = make_state()
    state.collect_action(
        Phase.DEBATE,
        {"type": ActionType.DEBATE, "agent_id": "health-minister", "message": "Health can wait."},
    )
    state.collect_action(
        Phase.PROPOSAL,
        {
            "type": ActionType.PROPOSE_BUDGET,
            "agent_id": "social-minister",
            "department": "Social",
            "amount": 15,
            "justification": "Public works",
        },
    )
    proposal_id = state.proposals[0].proposal_id
    state.collect_action(
        Phase.VOTING,
        {"type": ActionType.VOTE, "agent_id": "agriculture-minister", "proposal_id": proposal_id, "vote": "YES"},
    )
    state.collect_action(
        Phase.VOTING,
        {"type": ActionType.VOTE, "agent_id": "health-minister", "proposal_id": proposal_id, "vote": "YES"},
    )

    result = state.resolve()

    assert result.allocations["Social"] == 15.0
    assert state.debate_messages[0].message == "Health can wait."
    assert isinstance(state.proposals[0], Proposal)
    assert isinstance(state.votes[0], VoteRecord)


def test_collect_action_routes_abstain_from_proposal():
    state = make_state()

    abstention = state.collect_action(
        Phase.PROPOSAL,
        {"type": ActionType.ABSTAIN_FROM_PROPOSAL, "agent_id": "health-minister"},
    )

    assert isinstance(abstention, ProposalAbstention)
    assert abstention.agent_id == "health-minister"
    assert abstention.department == "Health"
    assert state.proposal_abstentions == [abstention]
