import pytest

from schemas.metrics import EpisodeMetrics
from telemetry.metrics_collector import MetricsCollector
from telemetry.run_summary import RunSummary


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
    collector.record_revenue_factor(1.2)
    collector.record_revenue_factor(1.6)
    collector.record_treasury(1000.0)
    collector.record_treasury(1200.0)
    collector.record_productivity(1.0)
    collector.record_debate_message()
    collector.record_proposal_passed()
    collector.record_final_state(
        final_treasury=1200.0,
        final_prosperity=1600.0,
        final_productivity=1.2,
        termination_reason="critical_failure",
        rounds_survived=5,
    )

    summary = collector.build_summary("episode-1")

    assert summary.episode_id == "episode-1"
    assert summary.total_reward == 10.0
    assert summary.rounds_survived == 5
    assert summary.final_treasury == 1200.0
    assert summary.final_prosperity == 1600.0
    assert summary.final_productivity == 1.2
    assert summary.termination_reason == "critical_failure"
    assert summary.prompt_tokens == 12
    assert summary.completion_tokens == 8
    assert summary.total_tokens == 25
    assert summary.critical_failure_count == 1
    assert summary.bankruptcy_count == 0
    assert summary.shutdown_count == 0
    assert summary.average_revenue_factor == pytest.approx(1.4)
    assert summary.treasury_stability == 10000.0
    assert summary.productivity_growth == pytest.approx(0.2)
    assert summary.debate_message_count == 1
    assert summary.proposals_passed_count == 1


def test_metrics_collector_uses_explicit_total_tokens() -> None:
    collector = MetricsCollector()

    collector.record_llm_tokens(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=20,
    )

    assert collector.prompt_tokens == 10
    assert collector.completion_tokens == 5
    assert collector.total_tokens == 20


def test_run_summary_aggregates_evaluation_metrics() -> None:
    summary = RunSummary(
        run_id="run-1",
        episodes=(
            EpisodeMetrics(
                episode_id="episode-1",
                rounds_survived=5,
                total_reward=10.0,
                final_prosperity=1000.0,
                critical_failure_count=1,
                average_revenue_factor=1.2,
                treasury_stability=25.0,
                productivity_growth=0.1,
                invalid_action_count=2,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                debate_message_count=3,
                proposals_passed_count=1,
            ),
            EpisodeMetrics(
                episode_id="episode-2",
                rounds_survived=7,
                total_reward=14.0,
                final_prosperity=1400.0,
                shutdown_count=1,
                average_revenue_factor=1.4,
                treasury_stability=75.0,
                productivity_growth=0.3,
                parse_error_count=1,
                prompt_tokens=20,
                completion_tokens=10,
                total_tokens=30,
                debate_message_count=5,
                proposals_passed_count=2,
            ),
        ),
    )

    assert summary.episode_count == 2
    assert summary.mean_total_reward == 12.0
    assert summary.mean_rounds_survived == 6.0
    assert summary.critical_failure_rate == 0.5
    assert summary.bankruptcy_rate == 0.0
    assert summary.shutdown_rate == 0.5
    assert summary.mean_final_prosperity == 1200.0
    assert summary.mean_average_revenue_factor == pytest.approx(1.3)
    assert summary.mean_treasury_stability == 50.0
    assert summary.mean_productivity_growth == pytest.approx(0.2)
    assert summary.invalid_action_count == 2
    assert summary.parse_error_count == 1
    assert summary.prompt_tokens == 30
    assert summary.completion_tokens == 15
    assert summary.total_tokens == 45
    assert summary.debate_message_count == 8
    assert summary.proposals_passed_count == 3
