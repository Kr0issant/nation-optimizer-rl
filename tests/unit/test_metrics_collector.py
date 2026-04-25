from telemetry.metrics_collector import MetricsCollector


def test_metrics_collector_accumulates_rewards() -> None:
    collector = MetricsCollector()

    collector.record_reward(2.5, round_number=1)
    collector.record_step(3.0, round_number=4)
    collector.record_reward(-1.0)

    assert collector.total_reward == 4.5
    assert collector.rounds_survived == 4


def test_metrics_collector_records_invalid_actions() -> None:
    collector = MetricsCollector()

    collector.record_action_validation(is_valid=True)
    collector.record_action_validation(is_valid=False)
    collector.record_invalid_action(parse_error=True)

    assert collector.invalid_action_count == 2
    assert collector.parse_error_count == 1


def test_metrics_collector_builds_final_summary() -> None:
    collector = MetricsCollector()
    collector.record_reward(10.0, round_number=3)
    collector.record_llm_tokens(prompt_tokens=12, completion_tokens=8)
    collector.record_llm_tokens(total_tokens=5)
    collector.record_final_state(
        final_treasury=1200.0,
        final_prosperity=1600.0,
        final_productivity=1.2,
        termination_reason="max_rounds",
        rounds_survived=5,
    )

    summary = collector.build_summary("episode-1")

    assert summary.episode_id == "episode-1"
    assert summary.total_reward == 10.0
    assert summary.rounds_survived == 5
    assert summary.final_treasury == 1200.0
    assert summary.final_prosperity == 1600.0
    assert summary.final_productivity == 1.2
    assert summary.termination_reason == "max_rounds"
    assert summary.prompt_tokens == 12
    assert summary.completion_tokens == 8
    assert summary.total_tokens == 25
