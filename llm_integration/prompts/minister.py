"""
System prompt generation for the parliamentary minister LLM.
"""

import json
from typing import Any

from schemas.observations import Observation
from llm_integration.context_builder import build_public_observation
from llm_integration.schemas import (
    LLMDebateAction, 
    LLMProposeBudgetAction, 
    LLMVoteAction, 
    LLMAbstainAction,
    LLMFinishDebateAction
)

def _get_schemas_dict(valid_actions: set[str]) -> list[dict[str, Any]]:
    """Returns the JSON schema definitions for the allowed actions."""
    schemas = []
    if "DEBATE" in valid_actions:
        schemas.append(LLMDebateAction.model_json_schema())
    if "PROPOSE_BUDGET" in valid_actions:
        schemas.append(LLMProposeBudgetAction.model_json_schema())
    if "VOTE" in valid_actions:
        schemas.append(LLMVoteAction.model_json_schema())
    if "ABSTAIN_FROM_PROPOSAL" in valid_actions:
        schemas.append(LLMAbstainAction.model_json_schema())
    if "FINISH_DEBATE" in valid_actions:
        schemas.append(LLMFinishDebateAction.model_json_schema())
    return schemas

def render_minister_prompt(
    observation: Observation,
    agent_id: str,
    valid_actions: set[str],
) -> str:
    """Render a strict JSON prompt for a parliamentary minister."""
    obs_dict = build_public_observation(observation)
    
    action_names = sorted(valid_actions)
    action_schemas = _get_schemas_dict(valid_actions)
    
    # Format debate history as a transcript (Limit to last 10 messages to save context)
    debate_history = ""
    messages = obs_dict.get("debate_messages", [])
    if messages:
        visible_messages = messages[-10:]
        debate_history = "\n--- PARLIAMENTARY DEBATE TRANSCRIPT (LAST 10 MESSAGES) ---\n"
        if len(messages) > 10:
            debate_history += "... (older messages truncated) ...\n"
        for msg in visible_messages:
            debate_history += f"Minister for {msg.get('agent_id')}: {msg.get('message')}\n"
        debate_history += "--------------------------------------------------------\n"
    
    return (
        f"You are the Minister for the '{agent_id}' department in a national parliament.\n"
        "Your mission is to balance your department's interests with the collective prosperity of the nation.\n"
        "\nCURRENT TASK:\n"
        "1. READ the 'DEBATE HISTORY' below very carefully. See what other ministers are proposing.\n"
        "2. RESPOND to your colleagues. If someone suggested something you agree or disagree with, mention it. Do not just repeat yourself.\n"
        "3. PROPOSE your own departmental needs based on the events in the 'Observation State'. Every event has a 'severity' score (1-5):\n"
        "   - Severity 1-2: Minor; can be managed with standard budget.\n"
        "   - Severity 3-4: Moderate; requires serious reallocation.\n"
        "   - Severity 5: CRITICAL; the nation is failing, emergency response is mandatory.\n"
        "4. DECIDE on ONE action to take. If you are in the DEBATE phase, your message should be a natural continuation of the conversation.\n"
        "   - Use 'DEBATE' to talk to your colleagues.\n"
        "   - Use 'FINISH_DEBATE' ONLY when you believe a consensus has been reached or there is nothing left to discuss. This moves the parliament to the proposal phase immediately.\n"
        "   - NOTE: The parliament has a hard limit of 18 messages per round. After 18 messages, the debate will be terminated automatically.\n"
        "5. VOTING (If applicable):\n"
        "   - If 'target_proposal_id' is provided in the Observation State, you MUST focus your vote on that specific proposal.\n"
        "\nSTRICT CONSTRAINTS:\n"
        "- Return ONLY a JSON object. No prose outside the JSON.\n"
        f"- Valid action types: {json.dumps(action_names)}.\n"
        f"- Allowed JSON schemas:\n{json.dumps(action_schemas, indent=2)}\n"
        f"{debate_history}\n"
        f"Observation State (JSON):\n{json.dumps(obs_dict, indent=2)}\n"
        "\nFINAL STEP: Return the JSON object representing your decision."
    )
