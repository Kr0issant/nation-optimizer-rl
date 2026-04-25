"""
Logic to convert the raw NationEnvironment observation into a clean LLM context dictionary.
"""

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

def build_public_observation(observation: Any) -> dict[str, Any]:
    """Builds a public-facing observation for ministers."""
    # Handle both schemas.observations.Observation and server.models.ParliamentaryObservation
    phase_str = getattr(observation, "phase_name", getattr(getattr(observation, "phase", None), "name", "UNKNOWN"))
    
    return {
        "round": observation.round,
        "phase": phase_str,
        "treasury": observation.treasury,
        "event_ledger": [_sanitize_event(event) for event in observation.event_ledger],
        "proposals": [asdict(proposal) for proposal in observation.proposals],
        "votes": [asdict(vote) for vote in observation.votes],
        "debate_messages": list(observation.debate_messages),
        "own_department": {"name": observation.own_department.name} if observation.own_department else None,
        "termination": dict(observation.termination) if observation.termination else {},
    }

def build_oracle_observation(observation: Observation) -> dict[str, Any]:
    """Builds an oracle observation for the dictator (sees private metrics and event costs)."""
    return {
        **build_public_observation(observation),
        "oracle_own_department": asdict(observation.own_department) if observation.own_department else None,
        "event_ledger": [dict(event) for event in observation.event_ledger],
    }

def _sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Removes hidden fields from events unless cost is already public."""
    if event.get("cost") is not None:
        return {str(key): value for key, value in event.items()}
    return {
        str(key): value
        for key, value in event.items()
        if str(key).lower() not in HIDDEN_EVENT_FIELDS
    }
