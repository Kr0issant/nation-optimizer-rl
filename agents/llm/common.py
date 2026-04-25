"""Shared helpers for strict, telemetry-rich LLM policy adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.action_parser import ActionParseError, parse_action_json
from schemas.actions import (
    AbstainProposalAction,
    Action,
    ActionType,
    DebateAction,
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
    action = parse_action_json(completion)
    _validate_action(action, observation=observation, valid_actions=valid_actions, agent_id=agent_id)
    return action


def safe_fallback_action(observation: Observation, valid_actions: set[str]) -> Action:
    """Return the least invasive valid action for the current phase.

    Preference order follows the action-space guardrails: explicit proposal
    abstention when it is legal, otherwise a zero request, an abstaining vote,
    or a no-op public debate message. If no action type is valid, callers should
    skip policy inference for that phase instead of inventing a side channel.
    """
    if ActionType.ABSTAIN_FROM_PROPOSAL.value in valid_actions:
        return AbstainProposalAction(type=ActionType.ABSTAIN_FROM_PROPOSAL)
    if ActionType.PROPOSE_BUDGET.value in valid_actions:
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=observation.own_department.name,
            amount=0.0,
            justification=SAFE_FALLBACK_JUSTIFICATION,
        )
    if ActionType.VOTE.value in valid_actions and observation.proposals:
        return VoteAction(
            type=ActionType.VOTE,
            proposal_id=observation.proposals[0].proposal_id,
            vote=VoteChoice.ABSTAIN,
        )
    if ActionType.DEBATE.value in valid_actions:
        return DebateAction(type=ActionType.DEBATE, message=SAFE_FALLBACK_DEBATE)
    raise LLMActionError("No safe fallback action is valid for this phase.")


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


def _validate_action(
    action: Action,
    *,
    observation: Observation,
    valid_actions: set[str],
    agent_id: str,
) -> None:
    if action.type.value not in valid_actions:
        raise ActionParseError(f"{action.type.value} is not valid in this phase.")
    if isinstance(action, ProposeBudgetAction):
        if action.department != observation.own_department.name:
            raise ActionParseError("PROPOSE_BUDGET department must match the agent portfolio.")
        if action.amount < 0 or action.amount > observation.treasury:
            raise ActionParseError("PROPOSE_BUDGET amount must be within the visible treasury.")
    if isinstance(action, VoteAction):
        proposal_ids = {proposal.proposal_id for proposal in observation.proposals}
        if action.proposal_id not in proposal_ids:
            raise ActionParseError("VOTE proposal_id must refer to an observed proposal.")
    if isinstance(action, DebateAction) and not action.message.strip():
        raise ActionParseError("DEBATE message must be non-empty.")
    if not agent_id.strip():
        raise ActionParseError("agent_id must be non-empty.")


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
