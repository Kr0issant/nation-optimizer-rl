"""Prompt helpers for JSON-constrained LLM adapters."""

from schemas.observations import Observation


def render_action_prompt(observation: Observation, agent_id: str) -> str:
    """Render a compact prompt that asks for one strict JSON action."""
    return (
        f"You are minister {agent_id}.\n"
        f"Round: {observation.round}\n"
        f"Phase: {observation.phase.name}\n"
        f"Treasury: {observation.treasury}\n"
        f"Your department: {observation.own_department.name}\n"
        "Return exactly one JSON object matching the valid action schema."
    )
