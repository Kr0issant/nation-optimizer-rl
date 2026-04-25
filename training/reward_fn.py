"""GRPO reward function for the parliamentary adapter.

The function returned by :func:`make_reward_fn` matches TRL's ``GRPOTrainer``
contract::

    reward_fn(prompts: list[str], completions: list[str], **kwargs) -> list[float]

``kwargs`` forwards every column of the training dataset alongside the prompt,
so the per-row context (treasury, own sector thresholds, proposals, valid
actions) is passed through unchanged from
:mod:`scripts.collect_grpo_prompts`.

Scoring is dense and grounded in the engine's piecewise revenue curve from
:mod:`core.revenue` so the reward signal is in lockstep with the simulator the
trained adapter will be evaluated against. There is no ``DEBATE`` branch —
debate is inference only and never enters the GRPO dataset.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from core.revenue import revenue_factor as _revenue_factor
from llm_integration.parsers import ActionParseError, parse_action_json
from schemas.actions import (
    AbstainProposalAction,
    Action,
    ActionType,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)

PARSE_FAIL_REWARD = -1.0
ILLEGAL_ACTION_REWARD = -0.5
ABSTAIN_REWARD = 0.0
PROPOSE_BASE_REWARD = 0.2
PROPOSE_FACTOR_WEIGHT = 0.9


def make_reward_fn() -> Callable[..., list[float]]:
    """Build the GRPO-compatible reward callable for parliamentary completions.

    Each call receives one prompt/completion pair plus per-row metadata through
    ``kwargs``. The returned scalar is a dense reward in roughly ``[-1.0, +1.4]``
    based on:

    1. JSON parses against :func:`parse_action_json`.
    2. Action type is in the per-row ``valid_actions`` list (legality check).
    3. Departmental and treasury constraints are satisfied (for proposals).
    4. The piecewise revenue factor of the proposed allocation, or of the
       proposal being voted on, taken from :func:`core.revenue.revenue_factor`.
    """

    def reward(
        prompts: Sequence[str],
        completions: Sequence[Any],
        **kwargs: Any,
    ) -> list[float]:
        rows = _materialise_rows(len(completions), kwargs)
        scores: list[float] = []
        for completion, row in zip(completions, rows, strict=True):
            text = _completion_to_text(completion)
            scores.append(_score_one(text, row))
        return scores

    return reward


def _score_one(completion: str, row: Mapping[str, Any]) -> float:
    try:
        action = parse_action_json(completion)
    except ActionParseError:
        return PARSE_FAIL_REWARD

    valid_actions = set(_ensure_iterable(row.get("valid_actions") or ()))
    if action.type.value not in valid_actions:
        return ILLEGAL_ACTION_REWARD

    if isinstance(action, ProposeBudgetAction):
        return _score_propose_budget(action, row)
    if isinstance(action, VoteAction):
        return _score_vote(action, row)
    if isinstance(action, AbstainProposalAction):
        return ABSTAIN_REWARD
    return ABSTAIN_REWARD


def _score_propose_budget(action: ProposeBudgetAction, row: Mapping[str, Any]) -> float:
    agent_id = str(row.get("agent_id", ""))
    if action.department != agent_id:
        return ILLEGAL_ACTION_REWARD

    treasury = _safe_float(row.get("treasury"), default=0.0)
    if not 0.0 <= float(action.amount) <= treasury:
        return ILLEGAL_ACTION_REWARD

    own_sector = _coerce_sector(row.get("own_sector"))
    rf = _piecewise_revenue_factor_for_amount(action.amount, own_sector)
    return PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (rf - 1.0)


def _score_vote(action: VoteAction, row: Mapping[str, Any]) -> float:
    proposals = row.get("proposals") or ()
    proposal = next(
        (p for p in proposals if str(p.get("proposal_id", "")) == action.proposal_id),
        None,
    )
    if proposal is None:
        return ILLEGAL_ACTION_REWARD

    sectors = _coerce_sector_map(row.get("all_sectors") or {})
    target = sectors.get(str(proposal.get("department", "")))
    if target is None:
        return ILLEGAL_ACTION_REWARD

    rf = _piecewise_revenue_factor_for_amount(
        _safe_float(proposal.get("amount"), default=0.0),
        target,
    )

    if action.vote is VoteChoice.YES:
        return rf - 1.0
    if action.vote is VoteChoice.NO:
        return -(rf - 1.0)
    return ABSTAIN_REWARD


def _piecewise_revenue_factor_for_amount(
    amount: float,
    sector: Mapping[str, float],
) -> float:
    """Wrap :func:`core.revenue.revenue_factor`, treating critical-failure as 0.0."""
    critical = float(sector["critical"])
    demand = float(sector["demand"])
    surplus = float(sector["surplus"])
    # Match core.config.WASTAGE_RATIO = 2.5
    wastage = demand * 2.5
    rf = _revenue_factor(
        allocation=float(amount),
        critical=critical,
        demand=demand,
        surplus=surplus,
        wastage=wastage,
    )
    return 0.0 if rf is None else float(rf)


def _coerce_sector(value: Any) -> Mapping[str, float]:
    if value is None:
        raise ValueError("Reward row is missing 'own_sector'.")
    if not isinstance(value, Mapping):
        raise TypeError("'own_sector' must be a mapping with critical/demand/surplus.")
    for required in ("critical", "demand", "surplus"):
        if required not in value:
            raise KeyError(f"'own_sector' is missing required key {required!r}.")
    return value


def _coerce_sector_map(value: Any) -> dict[str, Mapping[str, float]]:
    if not isinstance(value, Mapping):
        raise TypeError("'all_sectors' must be a mapping of sector name to thresholds.")
    return {str(name): _coerce_sector(sector) for name, sector in value.items()}


def _materialise_rows(count: int, kwargs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Re-stack TRL's column-major kwargs into one dict per completion."""
    if not count:
        return []
    rows: list[dict[str, Any]] = [dict() for _ in range(count)]
    for column, values in kwargs.items():
        if not _is_per_row_column(values, count):
            continue
        for index, value in enumerate(values):
            rows[index][column] = value
    return rows


def _is_per_row_column(values: Any, count: int) -> bool:
    if isinstance(values, (str, bytes, Mapping)):
        return False
    try:
        return len(values) == count  # type: ignore[arg-type]
    except TypeError:
        return False


def _completion_to_text(completion: Any) -> str:
    """Accept either raw strings or chat-style ``[{role,content}]`` outputs."""
    if isinstance(completion, str):
        return completion
    if isinstance(completion, Mapping):
        return str(completion.get("content") or completion.get("text") or "")
    if isinstance(completion, Sequence):
        for chunk in reversed(list(completion)):
            if isinstance(chunk, Mapping) and chunk.get("role") == "assistant":
                return str(chunk.get("content") or "")
        if completion:
            tail = completion[-1]
            if isinstance(tail, Mapping):
                return str(tail.get("content") or tail.get("text") or "")
            return str(tail)
    return str(completion)


def _ensure_iterable(value: Any) -> Iterable[str]:
    if isinstance(value, (str, bytes)):
        return [str(value)]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    return [str(value)]


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "ABSTAIN_REWARD",
    "ILLEGAL_ACTION_REWARD",
    "PARSE_FAIL_REWARD",
    "PROPOSE_BASE_REWARD",
    "PROPOSE_FACTOR_WEIGHT",
    "make_reward_fn",
]
