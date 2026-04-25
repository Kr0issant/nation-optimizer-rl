import json

from schemas.actions import ActionType, DebateAction
from schemas.phases import Phase
from schemas.rewards import RewardInfo
from telemetry import EpisodeLogger
from telemetry.jsonl_writer import JsonlWriter


def test_episode_logger_keeps_events_in_memory() -> None:
    logger = EpisodeLogger(episode_id="episode-1")
    event = logger.log_action_selected(
        DebateAction(type=ActionType.DEBATE, message="Fund Health."),
        round_number=2,
        phase=Phase.DEBATE,
        agent_id="Health",
    )

    assert event.episode_id == "episode-1"
    assert event.event_type == "action_selected"
    assert event.round == 2
    assert event.phase == 2
    assert event.agent_id == "Health"
    assert logger.events == [event]


def test_episode_logger_writes_jsonl(tmp_path) -> None:
    output_path = tmp_path / "episode.jsonl"
    logger = EpisodeLogger(
        episode_id="episode-1",
        writer=JsonlWriter(output_path),
    )

    logger.log_action_selected(
        DebateAction(type=ActionType.DEBATE, message="Fund Health."),
        round_number=1,
        phase=Phase.DEBATE,
        agent_id="Health",
    )

    line = output_path.read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert set(record) == {
        "agent_id",
        "episode_id",
        "event_id",
        "event_type",
        "payload",
        "phase",
        "round",
        "timestamp",
    }
    assert record["episode_id"] == "episode-1"
    assert record["event_type"] == "action_selected"
    assert record["round"] == 1
    assert record["phase"] == 2
    assert record["agent_id"] == "Health"
    assert record["payload"]["action"]["message"] == "Fund Health."


def test_dataclass_payloads_serialize_correctly(tmp_path) -> None:
    output_path = tmp_path / "episode.jsonl"
    logger = EpisodeLogger(
        episode_id="episode-1",
        writer=JsonlWriter(output_path),
    )

    logger.log_reward(
        RewardInfo(total=4.5, survival_bonus=1.0),
        round_number=3,
        agent_id="Commerce",
    )

    record = json.loads(output_path.read_text(encoding="utf-8"))
    assert record["event_type"] == "reward"
    assert record["payload"]["reward"] == {
        "allocation_penalty": 0.0,
        "base_reward": 0.0,
        "critical_penalty": 0.0,
        "productivity_bonus": 0.0,
        "survival_bonus": 1.0,
        "total": 4.5,
    }


def test_jsonl_output_is_append_only(tmp_path) -> None:
    output_path = tmp_path / "episode.jsonl"
    first_logger = EpisodeLogger(
        episode_id="episode-1",
        writer=JsonlWriter(output_path),
    )
    second_logger = EpisodeLogger(
        episode_id="episode-2",
        writer=JsonlWriter(output_path),
    )

    first_logger.log_observation({"treasury": 1000}, round_number=1)
    second_logger.log_termination("max_rounds", round_number=50)

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [record["episode_id"] for record in records] == ["episode-1", "episode-2"]
    assert [record["event_type"] for record in records] == [
        "observation",
        "termination",
    ]
