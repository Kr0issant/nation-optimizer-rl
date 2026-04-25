from core.population import PopulationTracker


def test_population_updates_deterministically() -> None:
    tracker = PopulationTracker()

    assert tracker.update(productivity=1.0) == 1_003_000


def test_higher_productivity_increases_growth_relative_to_lower_productivity() -> None:
    low_productivity = PopulationTracker()
    high_productivity = PopulationTracker()

    assert high_productivity.update(1.5) > low_productivity.update(0.5)


def test_crisis_penalty_reduces_growth() -> None:
    normal = PopulationTracker()
    crisis = PopulationTracker()

    assert crisis.update(1.0, crisis_occurred=True) < normal.update(1.0)
