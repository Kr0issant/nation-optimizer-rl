"""
Logic to convert the raw NationEnvironment observation into a clean LLM context dictionary.
"""

from dataclasses import asdict, fields, is_dataclass
from typing import Any, Mapping
from schemas.observations import Observation


def _to_dict(obj: Any) -> Any:
    """Serialize a Pydantic model or a frozen dataclass to a plain dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    return obj

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

PUBLIC_SECTOR_FIELDS = ("critical", "demand", "surplus")

def build_public_observation(observation: Any) -> dict[str, Any]:
    """Builds a public-facing observation for ministers."""
    # Handle both schemas.observations.Observation and server.models.ParliamentaryObservation
    phase_str = getattr(observation, "phase_name", getattr(getattr(observation, "phase", None), "name", "UNKNOWN"))
    
    return {
        "round": observation.round,
        "phase": phase_str,
        "treasury": observation.treasury,
        "event_ledger": [_sanitize_event(event) for event in observation.event_ledger],
        "proposals": [_to_dict(proposal) for proposal in observation.proposals],
        "votes": [_to_dict(vote) for vote in observation.votes],
        "debate_messages": list(observation.debate_messages),
        "own_department": _to_dict(observation.own_department) if observation.own_department else None,
        "termination": dict(observation.termination) if observation.termination else {},
    }

def build_oracle_observation(observation: Observation) -> dict[str, Any]:
    """Builds an oracle observation for the dictator (sees private metrics and event costs)."""
    return {
        **build_public_observation(observation),
        "oracle_own_department": _to_dict(observation.own_department) if observation.own_department else None,
        "event_ledger": [dict(event) for event in observation.event_ledger],
    }

def build_sector_thresholds(state: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    """Return public per-sector ``(critical, demand, surplus)`` thresholds.

    The reward function uses these to score proposed allocations against the
    same piecewise revenue curve the engine evaluates during the budget
    execution phase. Only public fields are exposed; hidden event costs and
    private metrics are deliberately omitted.
    """
    sectors = state.get("sectors") or {}
    if not isinstance(sectors, Mapping):
        raise TypeError("state['sectors'] must be a mapping of sector name to sector dict.")

    thresholds: dict[str, dict[str, float]] = {}
    for name, sector in sectors.items():
        if not isinstance(sector, Mapping):
            raise TypeError(f"sector entry for {name!r} must be a mapping.")
        thresholds[str(name)] = {
            field: float(sector[field])
            for field in PUBLIC_SECTOR_FIELDS
        }
    return thresholds


def _sanitize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Removes hidden fields from events unless cost is already public."""
    if event.get("cost") is not None:
        return {str(key): value for key, value in event.items()}
    return {
        str(key): value
        for key, value in event.items()
        if str(key).lower() not in HIDDEN_EVENT_FIELDS
    }
