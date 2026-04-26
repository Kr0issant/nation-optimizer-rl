"""
Parsers to validate LLM JSON output against Pydantic schemas and convert them 
to internal environment Action objects.
"""

import json
from typing import Any
from pydantic import TypeAdapter, ValidationError

from schemas.actions import (
    Action,
    ActionType,
    DebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
    FinishDebateAction
)
from llm_integration.schemas import LLMAction

class ActionParseError(ValueError):
    """Raised when a model response cannot be converted to a valid action."""

_action_adapter = TypeAdapter(LLMAction)

def parse_action_json(payload: str | dict[str, Any], target_proposal_id: str | None = None) -> Action:
    """Parses a JSON string or dict into an internal Action object."""
    if isinstance(payload, str):
        payload = payload.strip()
        if payload.startswith("```json"):
            payload = payload[7:]
        elif payload.startswith("```"):
            payload = payload[3:]
        if payload.endswith("```"):
            payload = payload[:-3]
        payload = payload.strip()
        
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ActionParseError(f"Failed to parse JSON: {e}")
    else:
        data = payload
    if not isinstance(data, dict):
        raise ActionParseError("Action payload must be a JSON object.")

    # Validate against Pydantic schemas
    try:
        parsed_llm_action = _action_adapter.validate_python(data)
    except ValidationError as e:
        raise ActionParseError(f"JSON schema validation failed: {str(e)}")

    # Convert to internal Action objects
    action_type = parsed_llm_action.type

    if action_type == "DEBATE":
        return DebateAction(type=ActionType.DEBATE, message=parsed_llm_action.message)

    elif action_type == "PROPOSE_BUDGET":
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=parsed_llm_action.department,
            amount=parsed_llm_action.amount,
            justification=parsed_llm_action.justification,
        )

    elif action_type == "VOTE":
        final_id = target_proposal_id or getattr(
            parsed_llm_action, "proposal_id", None
        ) or str(data.get("proposal_id", "") or "")
        if not final_id:
            raise ActionParseError("VOTE action generated but no target_proposal_id was provided by the environment.")
            
        return VoteAction(
            type=ActionType.VOTE,
            proposal_id=final_id,
            vote=VoteChoice(parsed_llm_action.vote),
        )


    elif action_type == "FINISH_DEBATE":
        return FinishDebateAction(type=ActionType.FINISH_DEBATE, reason=parsed_llm_action.reason)

    raise ActionParseError(f"Unsupported action type: {action_type}")
