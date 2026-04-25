"""
System prompt generation for the central planner (dictator) LLM.
"""

import json

from schemas.observations import Observation
from llm_integration.context_builder import build_oracle_observation, build_public_observation
from llm_integration.prompts.minister import _get_schemas_dict

def render_dictator_prompt(
    observation: Observation,
    agent_id: str,
    valid_actions: set[str],
    oracle: bool = False,
) -> str:
    """Render a strict JSON prompt for a central planning dictator."""
    obs_dict = build_oracle_observation(observation) if oracle else build_public_observation(observation)
    action_names = sorted(valid_actions)
    action_schemas = _get_schemas_dict(valid_actions)
    
    return (
        f"You are the Central Planning Dictator. You are currently acting on behalf of the '{agent_id}' department.\n"
        "You are participating in a multi-round economic simulation.\n"
        "You must analyze the current state of the nation, the events, and the overall needs of the state.\n"
        "You may only suggest ONE structured environment action; the game engine validates it.\n"
        "Use only the observation JSON below. Do not infer or invent hidden event costs.\n"
        f"Valid action types for this phase: {json.dumps(action_names)}.\n"
        f"Allowed JSON schemas:\n{json.dumps(action_schemas, indent=2)}\n"
        f"Observation:\n{json.dumps(obs_dict, indent=2)}\n"
        "Return exactly one JSON object matching ONE of the allowed schemas. Do not include prose, markdown formatting, or code fences."
    )
