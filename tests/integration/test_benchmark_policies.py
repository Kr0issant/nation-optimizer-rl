import json

import pytest

from evaluation.benchmark_policies import run_benchmarks
from telemetry.plotter import plot_benchmark_payload


def test_benchmark_runs_all_rule_based_baselines_with_disabled_events() -> None:
    payload = run_benchmarks(seeds=(7,), max_rounds=1, disable_events=True)

    assert payload["seeds"] == [7]
    assert payload["max_rounds"] == 1
    assert payload["events"] == "disabled"
    assert [policy["policy"] for policy in payload["policies"]] == [
        "random",
        "greedy",
        "equal_split",
        "conservative",
        "optimal_zone",
    ]
    for policy in payload["policies"]:
        assert policy["summary"]["episode_count"] == 1
        assert "mean_episode_return" in policy["summary"]
        assert "mean_survival_rounds" in policy["summary"]
        assert "mean_final_prosperity" in policy["summary"]
        assert policy["episodes"][0]["termination_reason"] is not None


def test_plotter_writes_pngs_from_benchmark_payload(tmp_path) -> None:
    pytest.importorskip("matplotlib")
    payload = run_benchmarks(seeds=(7,), max_rounds=1, disable_events=True)

    output_paths = plot_benchmark_payload(payload, tmp_path)

    assert [path.name for path in output_paths] == [
        "baseline_mean_episode_return.png",
        "baseline_survival_rounds.png",
    ]
    for path in output_paths:
        assert path.exists()
        assert path.stat().st_size > 0


def test_benchmark_payload_is_json_serializable() -> None:
    payload = run_benchmarks(seeds=(7,), max_rounds=1, disable_events=True)

    assert json.loads(json.dumps(payload))["run_id"] == "rule_based_baselines"
