"""Prompt helpers for JSON-constrained LLM adapters."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from schemas.observations import Observation

HIDDEN_EVENT_FIELDS = frozenset(
    {
        "cost",
        "exact_cost",
        "base_cost",
        "base_cost_impact",
        "severity_multiplier",
        "random_variance",
    }
)


def render_action_prompt(
    observation: Observation,
    agent_id: str,
    valid_actions: set[str] | frozenset[str] | None = None,
    *,
    role: str = "minister",
    oracle: bool = False,
) -> str:
    """Render a compact prompt that asks for one strict JSON action."""
    prompt_observation = (
        _oracle_observation(observation)
        if oracle
        else _public_observation(observation)
    )
    action_names = sorted(valid_actions or [])
    action_schemas = _valid_action_schemas(action_names)
    return (
        f"You are the {role} for agent {agent_id}.\n"
        "You may only suggest one structured environment action; the game engine validates it.\n"
        "Use only the observation JSON below. Do not infer or invent hidden event costs.\n"
        f"Valid action types now: {json.dumps(action_names)}.\n"
        f"Allowed JSON schemas: {json.dumps(action_schemas, sort_keys=True)}.\n"
        f"Observation: {json.dumps(prompt_observation, sort_keys=True)}.\n"
        "Return exactly one JSON object and no prose, markdown, or code fences."
    )


def _public_observation(observation: Observation) -> dict[str, Any]:
    return {
        "round": observation.round,
        "phase": observation.phase.name,
        "treasury": observation.treasury,
        "event_ledger": [_sanitize_event(event) for event in observation.event_ledger],
        "proposals": [asdict(proposal) for proposal in observation.proposals],
        "votes": [asdict(vote) for vote in observation.votes],
        "debate_messages": list(observation.debate_messages),
        "own_department": {"name": observation.own_department.name},
        "termination": dict(observation.termination),
    }


def _oracle_observation(observation: Observation) -> dict[str, Any]:
    return {
        **_public_observation(observation),
        "oracle_own_department": asdict(observation.own_department),
        "event_ledger": [dict(event) for event in observation.event_ledger],
    }


def _sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    if event.get("cost") is not None:
        return {str(key): value for key, value in event.items()}
    return {
        str(key): value
        for key, value in event.items()
        if str(key).lower() not in HIDDEN_EVENT_FIELDS
    }


def _valid_action_schemas(action_names: list[str]) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    if "DEBATE" in action_names:
        schemas.append({"type": "DEBATE", "message": "public message"})
    if "PROPOSE_BUDGET" in action_names:
        schemas.append(
            {
                "type": "PROPOSE_BUDGET",
                "department": "own department name",
                "amount": 0,
                "justification": "public justification",
            }
        )
    if "ABSTAIN_FROM_PROPOSAL" in action_names:
        schemas.append({"type": "ABSTAIN_FROM_PROPOSAL"})
    if "VOTE" in action_names:
        schemas.append(
            {
                "type": "VOTE",
                "proposal_id": "observed proposal id",
                "vote": "YES | NO | ABSTAIN",
            }
        )
    return schemas
