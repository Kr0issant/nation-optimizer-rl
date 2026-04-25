"""Central episode logger used by evaluation and training pipelines."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from telemetry.events import TelemetryEvent
from telemetry.jsonl_writer import JsonlWriter


class EpisodeLogger:
    def __init__(
        self,
        episode_id: str,
        writer: JsonlWriter | None = None,
    ) -> None:
        self.episode_id = episode_id
        self.writer = writer
        self.events: list[TelemetryEvent] = []

    def log(self, event_type: str, **payload: Any) -> TelemetryEvent:
        event = TelemetryEvent(
            event_type=event_type,
            episode_id=self.episode_id,
            payload={key: _serialize(value) for key, value in payload.items()},
        )
        self.events.append(event)
        if self.writer is not None:
            self.writer.write(event.to_dict())
        return event


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value
