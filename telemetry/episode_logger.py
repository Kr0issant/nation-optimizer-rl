"""Central episode logger used by evaluation and training pipelines."""

from __future__ import annotations

from typing import Any
from warnings import warn

from telemetry.events import TelemetryEvent, TelemetryEventType, normalize_event_type, serialize_value
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

    def log(
        self,
        event_type: TelemetryEventType | str,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
        payload: dict[str, Any] | None = None,
        **payload_fields: Any,
    ) -> TelemetryEvent:
        if "round" in payload_fields and round_number is None:
            warn(
                "Use round_number=... instead of payload field round=....",
                DeprecationWarning,
                stacklevel=2,
            )
            round_number = payload_fields.pop("round")
        if "phase" in payload_fields and phase is None:
            warn(
                "Use phase=... as a top-level logger argument.",
                DeprecationWarning,
                stacklevel=2,
            )
            phase = payload_fields.pop("phase")
        if "agent_id" in payload_fields and agent_id is None:
            warn(
                "Use agent_id=... as a top-level logger argument.",
                DeprecationWarning,
                stacklevel=2,
            )
            agent_id = payload_fields.pop("agent_id")

        serialized_payload = serialize_value(payload or {})
        serialized_payload.update(
            {key: serialize_value(value) for key, value in payload_fields.items()}
        )

        event = TelemetryEvent(
            event_type=normalize_event_type(event_type),
            episode_id=self.episode_id,
            round=round_number,
            phase=serialize_value(phase),
            agent_id=agent_id,
            payload=serialized_payload,
        )
        self.events.append(event)
        if self.writer is not None:
            self.writer.write(event.to_dict())
        return event

    def log_observation(
        self,
        observation: Any,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.OBSERVATION,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            observation=observation,
        )

    def log_action_selected(
        self,
        action: Any,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
        valid_actions: Any | None = None,
        raw_response: str | None = None,
    ) -> TelemetryEvent:
        payload = {"action": action}
        if valid_actions is not None:
            payload["valid_actions"] = valid_actions
        if raw_response is not None:
            payload["raw_response"] = raw_response
        return self.log(
            TelemetryEventType.ACTION_SELECTED,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            payload=payload,
        )

    def log_action_validated(
        self,
        *,
        is_valid: bool,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
        reason: str | None = None,
        action: Any | None = None,
    ) -> TelemetryEvent:
        payload: dict[str, Any] = {"is_valid": is_valid}
        if reason is not None:
            payload["reason"] = reason
        if action is not None:
            payload["action"] = action
        return self.log(
            TelemetryEventType.ACTION_VALIDATED,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            payload=payload,
        )

    def log_proposal(
        self,
        proposal: Any,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.PROPOSAL,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            proposal=proposal,
        )

    def log_vote(
        self,
        vote: Any,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.VOTE,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            vote=vote,
        )

    def log_reward(
        self,
        reward: Any,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.REWARD,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            reward=reward,
        )

    def log_treasury(
        self,
        treasury: float,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.TREASURY,
            round_number=round_number,
            phase=phase,
            treasury=treasury,
        )

    def log_prosperity(
        self,
        prosperity: float,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.PROSPERITY,
            round_number=round_number,
            phase=phase,
            prosperity=prosperity,
        )

    def log_productivity(
        self,
        productivity: float,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.PRODUCTIVITY,
            round_number=round_number,
            phase=phase,
            productivity=productivity,
        )

    def log_termination(
        self,
        termination_reason: str,
        *,
        round_number: int | None = None,
        phase: str | int | None = None,
        final_state: Any | None = None,
    ) -> TelemetryEvent:
        payload: dict[str, Any] = {"termination_reason": termination_reason}
        if final_state is not None:
            payload["final_state"] = final_state
        return self.log(
            TelemetryEventType.TERMINATION,
            round_number=round_number,
            phase=phase,
            payload=payload,
        )

    def log_llm_call(
        self,
        *,
        prompt: str | None = None,
        completion: str | None = None,
        parse_ok: bool | None = None,
        parse_error: str | None = None,
        parsed_action: Any | None = None,
        fallback_action: Any | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        round_number: int | None = None,
        phase: str | int | None = None,
        agent_id: str | None = None,
        model: str | None = None,
    ) -> TelemetryEvent:
        return self.log(
            TelemetryEventType.LLM_CALL,
            round_number=round_number,
            phase=phase,
            agent_id=agent_id,
            payload=_without_none(
                prompt=prompt,
                completion=completion,
                parse_ok=parse_ok,
                parse_error=parse_error,
                parsed_action=parsed_action,
                fallback_action=fallback_action,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=model,
            ),
        )


def _without_none(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
