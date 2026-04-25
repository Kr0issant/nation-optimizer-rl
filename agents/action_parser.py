"""Strict JSON parsing for LLM-produced actions."""

from __future__ import annotations

import json
from typing import Any

from schemas.actions import (
    AbstainProposalAction,
    Action,
    ActionType,
    DebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)


class ActionParseError(ValueError):
    """Raised when a model response cannot be converted to a valid action."""


def parse_action_json(payload: str | dict[str, Any]) -> Action:
    data = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(data, dict):
        raise ActionParseError("Action payload must be a JSON object.")

    try:
        action_type = ActionType(data["type"])
    except KeyError as exc:
        raise ActionParseError("Action payload missing required field: type.") from exc
    except ValueError as exc:
        raise ActionParseError(f"Unsupported action type: {data.get('type')!r}.") from exc

    if action_type is ActionType.DEBATE:
        return DebateAction(type=ActionType.DEBATE, message=_required_str(data, "message"))

    if action_type is ActionType.PROPOSE_BUDGET:
        amount = data.get("amount")
        if not isinstance(amount, int | float):
            raise ActionParseError("PROPOSE_BUDGET amount must be numeric.")
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=_required_str(data, "department"),
            amount=float(amount),
            justification=_required_str(data, "justification"),
        )

    if action_type is ActionType.VOTE:
        try:
            vote = VoteChoice(data["vote"])
        except KeyError as exc:
            raise ActionParseError("VOTE payload missing required field: vote.") from exc
        except ValueError as exc:
            raise ActionParseError(f"Unsupported vote choice: {data.get('vote')!r}.") from exc
        return VoteAction(
            type=ActionType.VOTE,
            proposal_id=_required_str(data, "proposal_id"),
            vote=vote,
        )

    return AbstainProposalAction(type=ActionType.ABSTAIN_FROM_PROPOSAL)


def _required_str(data: dict[str, Any], field_name: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ActionParseError(f"{field_name} must be a non-empty string.")
    return value
