from dataclasses import replace

import pytest

from core.config import GameConfig
from core.game import (
    PROPOSAL_STATUS_APPROVED,
    PROPOSAL_STATUS_REJECTED,
    PROPOSAL_STATUS_REJECTED_INVALID,
    NationGame,
)
from schemas.actions import ActionType, VoteChoice
from schemas.phases import Phase


DEPARTMENTS = ("Social", "Agriculture", "Health", "Education", "Defense", "Commerce")


def make_game(seed: int = 7, **config_overrides) -> NationGame:
    config = replace(GameConfig.from_json(), **config_overrides) if config_overrides else GameConfig.from_json()
    game = NationGame(config=config, seed=seed)
    game.event_engine._distribution = {"no_event": 1.0}
    game.reset()
    return game


def debate(agent_id: str = "Health") -> dict:
    return {"type": ActionType.DEBATE, "agent_id": agent_id, "message": "Public priority signal"}


def proposal(department: str, amount: float | None = None) -> dict:
    return {
        "type": ActionType.PROPOSE_BUDGET,
        "agent_id": department,
        "department": department,
        "amount": amount if amount is not None else 1.3 * GameConfig.from_json().SECTOR_BASELINES[department],
        "justification": "Fund expected demand",
    }


def vote(agent_id: str, proposal_id: str, choice: VoteChoice = VoteChoice.YES) -> dict:
    return {"type": ActionType.VOTE, "agent_id": agent_id, "proposal_id": proposal_id, "vote": choice}


def abstain_from_proposal(department: str) -> dict:
    return {
        "type": ActionType.ABSTAIN_FROM_PROPOSAL,
        "agent_id": department,
        "department": department,
    }


def advance_to_phase(game: NationGame, phase: Phase) -> None:
    while game.phase < phase and not game.done:
        if game.phase == Phase.DEBATE:
            game.force_advance_phase()
        else:
            game.step()


def submit_safe_proposals(game: NationGame) -> None:
    advance_to_phase(game, Phase.PROPOSAL)
    game.step([proposal(department) for department in DEPARTMENTS])


def approve_all_pending_proposals(game: NationGame) -> None:
    advance_to_phase(game, Phase.VOTING)
    actions = []
    for item in game.proposals:
        for department in DEPARTMENTS:
            if department != item.department:
                actions.append(vote(department, item.proposal_id))
    game.step(actions)


def run_phase_loop_round(game: NationGame) -> None:
    game.step()
    submit_safe_proposals(game)
    approve_all_pending_proposals(game)
    while game.phase != Phase.EVENT_REVELATION and not game.done:
        game.step()


def run_all_abstain_round(game: NationGame) -> None:
    advance_to_phase(game, Phase.PROPOSAL)
    game.step([abstain_from_proposal(department) for department in DEPARTMENTS])
    while game.phase != Phase.EVENT_REVELATION and not game.done:
        game.step()


def test_reset_creates_round_1_phase_1_state() -> None:
    game = make_game()

    state = game.state()

    assert state["round"] == 1
    assert state["phase"] == Phase.EVENT_REVELATION
    assert state["treasury"] == 1000


def test_phase_transitions_follow_1_through_9() -> None:
    game = make_game()
    seen = [game.phase]

    game.step()
    seen.append(game.phase)
    game.force_advance_phase()
    seen.append(game.phase)
    game.step([proposal(department) for department in DEPARTMENTS])
    seen.append(game.phase)
    approve_all_pending_proposals(game)
    seen.append(game.phase)
    while game.phase != Phase.EVENT_REVELATION:
        game.step()
        seen.append(game.phase)

    assert seen[:9] == [Phase(index) for index in range(1, 10)]
    assert game.round == 2


def test_debate_action_only_accepted_in_phase_2() -> None:
    game = make_game()

    phase_1_result = game.step(debate())
    phase_2_result = game.step(debate())

    assert phase_1_result.info["ignored_actions"][0]["reason"] == "wrong_phase"
    assert phase_2_result.info["accepted_actions"][0]["type"] == ActionType.DEBATE
    assert len(game.debate_messages) == 1


def test_proposal_action_only_accepted_in_phase_3() -> None:
    game = make_game()

    wrong_phase_result = game.step(proposal("Health"))
    advance_to_phase(game, Phase.PROPOSAL)
    accepted_result = game.step(proposal("Health"))

    assert wrong_phase_result.info["ignored_actions"][0]["reason"] == "wrong_phase"
    assert accepted_result.info["accepted_actions"][0]["type"] == ActionType.PROPOSE_BUDGET


def test_vote_action_only_accepted_in_phase_4() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)
    wrong_phase_result = game.step(vote("Health", "missing"))

    game = make_game()
    submit_safe_proposals(game)
    proposal_id = next(item.proposal_id for item in game.proposals if item.department != "Health")

    accepted_result = game.step(vote("Health", proposal_id))

    assert wrong_phase_result.info["ignored_actions"][0]["reason"] == "wrong_phase"
    assert accepted_result.info["accepted_actions"][0]["type"] == ActionType.VOTE


def test_wrong_phase_action_is_ignored() -> None:
    game = make_game()

    result = game.step({"type": ActionType.VOTE, "agent_id": "Health", "proposal_id": "missing", "vote": VoteChoice.YES})

    assert result.info["ignored_actions"][0]["reason"] == "wrong_phase"
    assert game.votes == []


def test_invalid_proposal_over_treasury_is_rejected() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)

    result = game.step(proposal("Health", amount=game.treasury.balance + 1))

    assert result.info["rejected_actions"][0]["reason"] == "exceeds_treasury"
    assert game.proposals[0].status == PROPOSAL_STATUS_REJECTED_INVALID


def test_duplicate_proposal_is_ignored() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)

    result = game.step([proposal("Health", amount=90), proposal("Health", amount=95)])

    assert len(game.proposals) == 1
    assert result.info["ignored_actions"][0]["reason"] == "duplicate_proposal"


def test_agents_cannot_propose_for_another_department() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)
    action = proposal("Health")
    action["agent_id"] = "Defense"

    result = game.step(action)

    assert result.info["rejected_actions"][0]["reason"] == "wrong_department"
    assert game.proposals[0].status == PROPOSAL_STATUS_REJECTED_INVALID


def test_self_vote_is_rejected() -> None:
    game = make_game()
    submit_safe_proposals(game)
    health_proposal = next(item for item in game.proposals if item.department == "Health")

    result = game.step(vote("Health", health_proposal.proposal_id))

    assert result.info["rejected_actions"][0]["reason"] == "self_vote"
    assert health_proposal.votes == {}


def test_tie_vote_rejects_proposal() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)
    game.step(proposal("Health", amount=90))
    health_proposal = game.proposals[0]
    game.force_advance_phase()

    game.step([
        vote("Agriculture", health_proposal.proposal_id, VoteChoice.ABSTAIN),
        vote("Defense", health_proposal.proposal_id, VoteChoice.YES),
        vote("Education", health_proposal.proposal_id, VoteChoice.ABSTAIN),
        vote("Commerce", health_proposal.proposal_id, VoteChoice.NO),
        vote("Social", health_proposal.proposal_id, VoteChoice.ABSTAIN),
    ])
    game.step()

    assert health_proposal.status == PROPOSAL_STATUS_REJECTED
    assert game.sectors["Health"].allocation == 0
    assert game.done


def test_approved_proposal_debits_treasury() -> None:
    game = make_game()
    submit_safe_proposals(game)
    approve_all_pending_proposals(game)

    before_execution = game.treasury.balance
    approved_total = sum(item.amount for item in game.proposals)
    game.step()

    assert all(item.status == PROPOSAL_STATUS_APPROVED for item in game.proposals)
    assert game.treasury.balance == pytest.approx(before_execution - approved_total)


def test_rejected_proposal_allocates_zero() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)
    game.step(proposal("Health", amount=90))
    health_proposal = game.proposals[0]
    game.force_advance_phase()
    game.step([
        vote(department, health_proposal.proposal_id, VoteChoice.NO)
        for department in DEPARTMENTS
        if department != "Health"
    ])

    game.step()

    assert health_proposal.status == PROPOSAL_STATUS_REJECTED
    assert game.sectors["Health"].allocation == 0
    assert game.done


def test_abstain_from_proposal_action_is_accepted() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)

    result = game.step(abstain_from_proposal("Health"))

    assert result.info["accepted_actions"][0]["type"] == ActionType.ABSTAIN_FROM_PROPOSAL
    assert game.proposals == []


def test_all_abstain_round_triggers_critical_failure() -> None:
    game = make_game()

    run_all_abstain_round(game)
    assert game.done
    assert game.termination_reason == "CRITICAL_FAILURE"


def test_sequential_treasury_depletion_rejects_later_proposal() -> None:
    game = make_game()
    advance_to_phase(game, Phase.PROPOSAL)
    game.step([proposal("Social", amount=900), proposal("Health", amount=900)])
    social_proposal = next(item for item in game.proposals if item.department == "Social")
    health_proposal = next(item for item in game.proposals if item.department == "Health")
    game.force_advance_phase()

    game.step(
        [
            vote(department, social_proposal.proposal_id)
            for department in DEPARTMENTS
            if department != "Social"
        ]
        + [
            vote(department, health_proposal.proposal_id)
            for department in DEPARTMENTS
            if department != "Health"
        ]
    )
    game.step()

    assert social_proposal.status == PROPOSAL_STATUS_APPROVED
    assert health_proposal.status == PROPOSAL_STATUS_REJECTED
    assert health_proposal.rejection_reason == "exceeds_remaining_treasury"
    assert game.done


def test_critical_under_allocation_terminates_episode() -> None:
    game = make_game()
    allocations = dict(game.config.SECTOR_BASELINES)
    allocations["Defense"] = 30

    result = game.step(allocations)

    assert result.done
    assert result.termination_reason == "CRITICAL_FAILURE"


def test_critical_failure_after_revenue_round_uses_zero_current_revenue() -> None:
    game = make_game()
    safe_allocations = {
        department: baseline * 1.3
        for department, baseline in game.config.SECTOR_BASELINES.items()
    }
    first_result = game.step(safe_allocations)
    assert first_result.total_revenue > 0

    advance_to_phase(game, Phase.PROPOSAL)
    game.step(proposal("Health", amount=1))
    health_proposal = game.proposals[0]
    game.force_advance_phase()
    game.step([
        vote(department, health_proposal.proposal_id)
        for department in DEPARTMENTS
        if department != "Health"
    ])
    result = game.step()

    assert result.done
    assert result.termination_reason == "CRITICAL_FAILURE"
    assert game.last_total_revenue == 0
    assert result.reward.critical_penalty < 0


def test_bankruptcy_terminates_episode() -> None:
    game = make_game()
    game.treasury.balance = 1
    critical_allocations = {
        department: baseline * game.config.CRITICAL_RATIO
        for department, baseline in game.config.SECTOR_BASELINES.items()
    }

    result = game.step(critical_allocations)

    assert result.done
    assert result.termination_reason == "BANKRUPTCY"
    assert result.treasury <= 0


def test_max_rounds_terminates_episode() -> None:
    game = make_game(MAX_ROUNDS=1)

    run_phase_loop_round(game)

    assert game.done
    assert game.termination_reason == "MAX_ROUNDS"


def test_seeded_reset_is_deterministic() -> None:
    first = NationGame(seed=123).reset(seed=123)
    second = NationGame(seed=123).reset(seed=123)

    assert first["event_ledger"] == second["event_ledger"]
    assert first["sectors"] == second["sectors"]
