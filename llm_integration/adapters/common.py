"""Shared helpers for strict, telemetry-rich LLM policy adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_integration.parsers import parse_action_json
from schemas.actions import (
    Action,
    ActionType,
    DebateAction,
    FinishDebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)
from schemas.observations import Observation
from telemetry import EpisodeLogger

SAFE_FALLBACK_DEBATE = "No additional public argument this turn."
SAFE_FALLBACK_JUSTIFICATION = "LLM parsing failed; submitting a safe zero request."


class LLMActionError(RuntimeError):
    """Raised when an LLM completion cannot produce an allowed action."""


@dataclass(frozen=True, slots=True)
class GenerationRecord:
    completion: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def parse_generation_result(result: Any) -> GenerationRecord:
    if isinstance(result, str):
        return GenerationRecord(completion=result)
    if isinstance(result, dict):
        return GenerationRecord(
            completion=str(
                result.get("completion")
                or result.get("generated_text")
                or result.get("text")
                or ""
            ),
            prompt_tokens=_optional_int(result.get("prompt_tokens")),
            completion_tokens=_optional_int(result.get("completion_tokens")),
            total_tokens=_optional_int(result.get("total_tokens")),
        )

    usage = getattr(result, "usage", None)
    prompt_tokens = getattr(result, "prompt_tokens", None)
    completion_tokens = getattr(result, "completion_tokens", None)
    total_tokens = getattr(result, "total_tokens", None)
    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
        completion_tokens = usage.get("completion_tokens", completion_tokens)
        total_tokens = usage.get("total_tokens", total_tokens)

    return GenerationRecord(
        completion=str(
            getattr(result, "completion", None)
            or getattr(result, "generated_text", None)
            or getattr(result, "text", "")
        ),
        prompt_tokens=_optional_int(prompt_tokens),
        completion_tokens=_optional_int(completion_tokens),
        total_tokens=_optional_int(total_tokens),
    )


def parse_allowed_action(
    completion: str,
    *,
    observation: Observation,
    valid_actions: set[str],
    agent_id: str,
) -> Action:
    target_proposal_id = getattr(observation, "target_proposal_id", None)
    action = parse_action_json(completion, target_proposal_id=target_proposal_id)
    if action.type.value not in valid_actions:
        raise LLMActionError(
            f"LLM generated action type '{action.type.value}', "
            f"but only {valid_actions} are allowed in this phase."
        )
    return action


def safe_fallback_action(observation: Observation, valid_actions: set[str]) -> Action:
<<<<<<< HEAD
    """Return the least harmful valid action for the current phase.

    Priority: propose a budget (keeps the game alive) > vote YES on pending
    proposals > debate > abstain > finish debate.  Abstaining during the
    proposal phase starves every sector and triggers critical failure, so
    ``PROPOSE_BUDGET`` must come first.
    """
=======
    """Return the least invasive valid action for the current phase."""
        
>>>>>>> f4a8456d1ed3b821152bf5374a478629e1ce1697
    if ActionType.PROPOSE_BUDGET.value in valid_actions:
        dept_name = (
            observation.own_department.name
            if observation.own_department
            else "Unknown"
        )
        n_depts = max(len(observation.proposals), 6)
        share = max(observation.treasury / n_depts, 1.0)
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=dept_name,
            amount=share,
            justification=SAFE_FALLBACK_JUSTIFICATION,
        )

    if ActionType.VOTE.value in valid_actions:
        # Prioritize the target_proposal_id from the environment
        target_id = getattr(observation, "target_proposal_id", None)
        if not target_id:
            # Fallback to the first pending proposal if target is missing
            pending_ids = [p.proposal_id for p in observation.proposals if p.status == "pending"]
            target_id = pending_ids[0] if pending_ids else "unknown_id"
        return VoteAction(
            type=ActionType.VOTE,
            proposal_id=target_id,
            vote=VoteChoice.YES,
        )

    if ActionType.DEBATE.value in valid_actions:
        return DebateAction(type=ActionType.DEBATE, message=SAFE_FALLBACK_DEBATE)

    if ActionType.ABSTAIN_FROM_PROPOSAL.value in valid_actions:
        return AbstainProposalAction(type=ActionType.ABSTAIN_FROM_PROPOSAL)

    if ActionType.FINISH_DEBATE.value in valid_actions:
        return FinishDebateAction(type=ActionType.FINISH_DEBATE, reason="Automatic timeout fallback.")

    raise LLMActionError(f"No safe fallback action is valid for this phase. Valid: {valid_actions}")


def log_llm_call(
    logger: EpisodeLogger | None,
    *,
    observation: Observation,
    agent_id: str,
    prompt: str,
    generation: GenerationRecord,
    parse_ok: bool,
    parse_error: str | None = None,
    parsed_action: Action | None = None,
    fallback_action: Action | None = None,
    model: str | None = None,
) -> None:
    if logger is None:
        return
    logger.log_llm_call(
        prompt=prompt,
        completion=generation.completion,
        parse_ok=parse_ok,
        parse_error=parse_error,
        parsed_action=parsed_action,
        fallback_action=fallback_action,
        prompt_tokens=generation.prompt_tokens,
        completion_tokens=generation.completion_tokens,
        total_tokens=generation.total_tokens,
        round_number=observation.round,
        phase=observation.phase,
        agent_id=agent_id,
        model=model,
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
