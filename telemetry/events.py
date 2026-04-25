"""Structured telemetry events emitted during rollouts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import uuid4


class TelemetryEventType(StrEnum):
    OBSERVATION = "observation"
    ACTION_SELECTED = "action_selected"
    ACTION_VALIDATED = "action_validated"
    REWARD = "reward"
    TERMINATION = "termination"
    LLM_CALL = "llm_call"
    RUN_SUMMARY = "run_summary"


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    event_type: str
    episode_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    round: int | None = None
    phase: str | int | None = None
    agent_id: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return serialize_value(asdict(self))


def normalize_event_type(event_type: TelemetryEventType | str) -> str:
    if isinstance(event_type, TelemetryEventType):
        return event_type.value
    return str(event_type)


def serialize_value(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return serialize_value(value.to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return serialize_value(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [serialize_value(item) for item in value]
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): serialize_value(item) for key, item in value.items()}
    return value
