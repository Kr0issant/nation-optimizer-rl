"""Round phases and action availability."""

from enum import IntEnum


class Phase(IntEnum):
    EVENT_REVELATION = 1
    DEBATE = 2
    PROPOSAL = 3
    VOTING = 4
    BUDGET_EXECUTION = 5
    CONSUMPTION_AND_EVENT_IMPACT = 6
    REVENUE_CALCULATION = 7
    SURPLUS_ROLLOVER = 8
    TERMINATION_CHECK = 9


ACTION_TYPES_BY_PHASE = {
    Phase.EVENT_REVELATION: frozenset(),
    Phase.DEBATE: frozenset({"DEBATE", "FINISH_DEBATE"}),
    Phase.PROPOSAL: frozenset({"PROPOSE_BUDGET"}),
    Phase.VOTING: frozenset({"VOTE"}),
    Phase.BUDGET_EXECUTION: frozenset(),
    Phase.CONSUMPTION_AND_EVENT_IMPACT: frozenset(),
    Phase.REVENUE_CALCULATION: frozenset(),
    Phase.SURPLUS_ROLLOVER: frozenset(),
    Phase.TERMINATION_CHECK: frozenset(),
}


def valid_action_types_for_phase(phase: Phase) -> frozenset[str]:
    return ACTION_TYPES_BY_PHASE[Phase(phase)]
