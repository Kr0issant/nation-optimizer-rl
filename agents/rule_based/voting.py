"""Shared vote-target selection for rule-based adapters."""

from schemas.observations import ProposalObservation


def is_vote_target(proposal: ProposalObservation, agent_id: str) -> bool:
    proposal_owner = proposal.agent_id or proposal.department
    return (
        proposal.status == "pending"
        and proposal.department != agent_id
        and proposal_owner != agent_id
        and agent_id not in proposal.votes
    )


def first_vote_target(
    proposals: tuple[ProposalObservation, ...],
    agent_id: str,
) -> ProposalObservation | None:
    return next(
        (proposal for proposal in proposals if is_vote_target(proposal, agent_id)),
        None,
    )
