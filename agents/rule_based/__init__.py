"""Rule-based baseline adapters."""

from agents.rule_based.conservative import ConservativeAdapter
from agents.rule_based.equal_split import EqualSplitAdapter
from agents.rule_based.greedy import GreedyAdapter
from agents.rule_based.optimal_zone import OptimalZoneAdapter

__all__ = [
    "ConservativeAdapter",
    "EqualSplitAdapter",
    "GreedyAdapter",
    "OptimalZoneAdapter",
]
