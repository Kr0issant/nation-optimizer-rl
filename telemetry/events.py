"""Structured telemetry events emitted during rollouts."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import uuid4

MAX_SERIALIZATION_DEPTH = 32


class TelemetryEventType(StrEnum):
    OBSERVATION = "observation"
    ACTION_SELECTED = "action_selected"
    ACTION_VALIDATED = "action_validated"
    PROPOSAL = "proposal"
    VOTE = "vote"
    REWARD = "reward"
    TREASURY = "treasury"
    PROSPERITY = "prosperity"
    PRODUCTIVITY = "productivity"
    TERMINATION = "termination"
    LLM_CALL = "llm_call"
    RUN_SUMMARY = "run_summary"


class TelemetrySerializationError(ValueError):
    """Raised when a telemetry payload cannot be safely serialized."""


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
        return {
            "event_id": self.event_id,
            "episode_id": self.episode_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "round": self.round,
            "phase": serialize_value(self.phase),
            "agent_id": self.agent_id,
            "payload": serialize_value(self.payload),
        }


def normalize_event_type(event_type: TelemetryEventType | str) -> str:
    if isinstance(event_type, TelemetryEventType):
        return event_type.value
    return str(event_type)


def serialize_value(
    value: Any,
    *,
    max_depth: int = MAX_SERIALIZATION_DEPTH,
    _seen: set[int] | None = None,
    _depth: int = 0,
) -> Any:
    if _depth > max_depth:
        raise TelemetrySerializationError("Telemetry payload exceeds maximum depth.")

    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, str | int | float | bool):
        return value

    seen = _seen if _seen is not None else set()
    value_id = id(value)
    if value_id in seen:
        raise TelemetrySerializationError("Telemetry payload contains a circular reference.")

    if hasattr(value, "to_dict") and callable(value.to_dict):
        seen.add(value_id)
        try:
            return serialize_value(
                value.to_dict(),
                max_depth=max_depth,
                _seen=seen,
                _depth=_depth + 1,
            )
        finally:
            seen.remove(value_id)

    if is_dataclass(value) and not isinstance(value, type):
        seen.add(value_id)
        try:
            return {
                field.name: serialize_value(
                    getattr(value, field.name),
                    max_depth=max_depth,
                    _seen=seen,
                    _depth=_depth + 1,
                )
                for field in fields(value)
            }
        finally:
            seen.remove(value_id)

    if isinstance(value, dict):
        seen.add(value_id)
        try:
            return {
                str(key): serialize_value(
                    item,
                    max_depth=max_depth,
                    _seen=seen,
                    _depth=_depth + 1,
                )
                for key, item in value.items()
            }
        finally:
            seen.remove(value_id)

    if isinstance(value, tuple | list):
        seen.add(value_id)
        try:
            return [
                serialize_value(
                    item,
                    max_depth=max_depth,
                    _seen=seen,
                    _depth=_depth + 1,
                )
                for item in value
            ]
        finally:
            seen.remove(value_id)

    if isinstance(value, set | frozenset):
        seen.add(value_id)
        try:
            return [
                serialize_value(
                    item,
                    max_depth=max_depth,
                    _seen=seen,
                    _depth=_depth + 1,
                )
                for item in sorted(value, key=repr)
            ]
        finally:
            seen.remove(value_id)

    return value
