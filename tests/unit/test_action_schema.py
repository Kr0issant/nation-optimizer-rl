import pytest

from llm_integration.parsers import ActionParseError, parse_action_json
from schemas.actions import ActionType, ProposeBudgetAction, VoteChoice
from schemas.phases import Phase, valid_action_types_for_phase


def test_propose_budget_action_parses_from_json() -> None:
    action = parse_action_json(
        """
        {
          "type": "PROPOSE_BUDGET",
          "department": "Health",
          "amount": 135,
          "justification": "Health crisis response"
        }
        """
    )

    assert isinstance(action, ProposeBudgetAction)
    assert action.department == "Health"
    assert action.amount == 135.0
    assert action.to_dict()["type"] == "PROPOSE_BUDGET"


def test_vote_action_parses_vote_choice() -> None:
    action = parse_action_json(
        {"type": "VOTE", "proposal_id": "proposal-1", "vote": "YES"}
    )

    assert action.vote is VoteChoice.YES


def test_invalid_amount_is_rejected() -> None:
    with pytest.raises(ActionParseError):
        parse_action_json(
            {
                "type": "PROPOSE_BUDGET",
                "department": "Health",
                "amount": "all of it",
                "justification": "invalid",
            }
        )


def test_phase_action_mapping_matches_spec() -> None:
    assert valid_action_types_for_phase(Phase.DEBATE) == frozenset({"DEBATE"})
    assert valid_action_types_for_phase(Phase.PROPOSAL) == frozenset(
        {"PROPOSE_BUDGET", "ABSTAIN_FROM_PROPOSAL"}
    )
    assert valid_action_types_for_phase(Phase.VOTING) == frozenset({"VOTE"})
    assert ActionType.DEBATE.value in valid_action_types_for_phase(Phase.DEBATE)
