import json

from schemas.actions import ActionType, DebateAction
from telemetry import EpisodeLogger
from telemetry.jsonl_writer import JsonlWriter


def test_episode_logger_keeps_events_in_memory() -> None:
    logger = EpisodeLogger(episode_id="episode-1")
    event = logger.log("action_selected", agent_id="Health", action="DEBATE")

    assert event.episode_id == "episode-1"
    assert event.payload["agent_id"] == "Health"
    assert logger.events == [event]


def test_episode_logger_writes_jsonl(tmp_path) -> None:
    output_path = tmp_path / "episode.jsonl"
    logger = EpisodeLogger(
        episode_id="episode-1",
        writer=JsonlWriter(output_path),
    )

    logger.log(
        "action_selected",
        action=DebateAction(type=ActionType.DEBATE, message="Fund Health."),
    )

    line = output_path.read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert record["event_type"] == "action_selected"
    assert record["payload"]["action"]["message"] == "Fund Health."
