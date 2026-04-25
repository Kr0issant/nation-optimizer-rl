import random

from core.events import Event, EventEngine, sector_multipliers


SECTORS = ["Social", "Agriculture", "Health", "Education", "Defense", "Commerce"]


def test_event_catalog_loads() -> None:
    engine = EventEngine()

    assert engine.catalog


def test_seeded_generation_is_deterministic() -> None:
    engine = EventEngine()

    first = [event.to_dict() for event in engine.generate_events(random.Random(7), SECTORS)]
    second = [event.to_dict() for event in engine.generate_events(random.Random(7), SECTORS)]

    assert first == second


def test_generated_events_are_max_length_two() -> None:
    engine = EventEngine()

    for seed in range(100):
        assert len(engine.generate_events(random.Random(seed), SECTORS)) <= 2


def test_sector_multiplier_aggregation_works() -> None:
    events = [
        Event(
            id="a",
            name="A",
            severity=2,
            affected_sectors={"Health": 2.0, "Commerce": 1.5},
            category="minor",
            narrative="A",
        ),
        Event(
            id="b",
            name="B",
            severity=3,
            affected_sectors={"Health": 1.5},
            category="moderate",
            narrative="B",
        ),
    ]

    assert sector_multipliers(events) == {"Health": 3.0, "Commerce": 1.5}


def test_no_event_category_returns_empty_list() -> None:
    engine = EventEngine()
    engine._distribution = {"no_event": 1.0}

    assert engine.generate_events(random.Random(1), SECTORS) == []
