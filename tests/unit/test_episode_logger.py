import json
from dataclasses import dataclass

import pytest

from schemas.actions import ActionType, DebateAction
from schemas.phases import Phase
from schemas.rewards import RewardInfo
from telemetry import EpisodeLogger
from telemetry.events import TelemetrySerializationError
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


def test_logger_rejects_circular_payloads(tmp_path) -> None:
    @dataclass
    class Node:
        name: str
        child: "Node | None" = None

    output_path = tmp_path / "episode.jsonl"
    logger = EpisodeLogger(
        episode_id="episode-1",
        writer=JsonlWriter(output_path),
    )
    parent = Node(name="parent")
    child = Node(name="child", child=parent)
    parent.child = child

    with pytest.raises(TelemetrySerializationError):
        logger.log_observation(parent, round_number=1)


def test_spec_required_helpers_emit_consistent_payloads(tmp_path) -> None:
    output_path = tmp_path / "episode.jsonl"
    logger = EpisodeLogger(
        episode_id="episode-1",
        writer=JsonlWriter(output_path),
    )

    logger.log_proposal({"proposal_id": "p1"}, round_number=2, agent_id="Health")
    logger.log_vote({"proposal_id": "p1", "vote": "YES"}, round_number=2)
    logger.log_treasury(950.0, round_number=2)
    logger.log_prosperity(1200.0, round_number=2)
    logger.log_productivity(1.1, round_number=2)

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [record["event_type"] for record in records] == [
        "proposal",
        "vote",
        "treasury",
        "prosperity",
        "productivity",
    ]
    assert records[0]["payload"] == {"proposal": {"proposal_id": "p1"}}
    assert records[1]["payload"] == {"vote": {"proposal_id": "p1", "vote": "YES"}}
    assert records[2]["payload"] == {"treasury": 950.0}
    assert records[3]["payload"] == {"prosperity": 1200.0}
    assert records[4]["payload"] == {"productivity": 1.1}
