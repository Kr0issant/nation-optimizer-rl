"""GRPO reward function for the parliamentary adapter.

The function returned by :func:`make_reward_fn` matches TRL's ``GRPOTrainer``
contract::

    reward_fn(prompts: list[str], completions: list[str], **kwargs) -> list[float]

``kwargs`` forwards every column of the training dataset alongside the prompt,
so the per-row context (treasury, own sector thresholds, proposals, valid
actions) is passed through unchanged from
:mod:`scripts.collect_grpo_prompts`.

Proposals are **discretionary** above auto-funded critical minimums (see
`specification/proposed-amendments` Option A). Scoring is dense and grounded in
:mod:`core.revenue` so the signal matches the simulator. There is no
``DEBATE`` branch — debate is inference only and never enters the GRPO dataset.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from core.config import WASTAGE_RATIO
from core.revenue import revenue_factor as _revenue_factor
from llm_integration.parsers import ActionParseError, parse_action_json
from schemas.actions import (
    ActionType,
    DebateAction,
    FinishDebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)

PARSE_FAIL_REWARD = -1.0
ILLEGAL_ACTION_REWARD = -0.5
VOTE_NEUTRAL_REWARD = 0.0
PROPOSE_BASE_REWARD = 0.2
PROPOSE_FACTOR_WEIGHT = 0.9
VOTE_YES_WEIGHT = 1.0
VOTE_NO_WEIGHT = 0.5
SURVIVAL_SHAPING_WEIGHT = 0.0


def _total_critical_from_row(row: Mapping[str, Any]) -> float:
    v = row.get("total_critical")
    if v is not None and str(v) != "":
        return max(0.0, _safe_float(v, default=0.0))
    sectors = row.get("all_sectors")
    if not isinstance(sectors, Mapping):
        return 0.0
    s = 0.0
    for data in sectors.values():
        if isinstance(data, Mapping) and "critical" in data:
            s += float(data["critical"])
    return s


def make_reward_fn() -> Callable[..., list[float]]:
    """Build the GRPO-compatible reward callable for parliamentary completions."""

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
        base = _score_propose_budget(action, row)
    elif isinstance(action, VoteAction):
        base = _score_vote(action, row)
    elif isinstance(action, (DebateAction, FinishDebateAction)):
        return VOTE_NEUTRAL_REWARD if action.type.value in valid_actions else ILLEGAL_ACTION_REWARD
    else:
        return ILLEGAL_ACTION_REWARD

    mr = int(row.get("max_rounds") or 0)
    r = int(row.get("round") or 0)
    if mr > 0 and SURVIVAL_SHAPING_WEIGHT:
        base += SURVIVAL_SHAPING_WEIGHT * (r / float(mr))
    return base


def _score_propose_budget(action: ProposeBudgetAction, row: Mapping[str, Any]) -> float:
    agent_id = str(row.get("agent_id", ""))
    if action.department != agent_id:
        return ILLEGAL_ACTION_REWARD

    treasury = _safe_float(row.get("treasury"), default=0.0)
    total_c = _total_critical_from_row(row)
    if not 0.0 <= float(action.amount) <= max(0.0, treasury - total_c):
        return ILLEGAL_ACTION_REWARD

    own_sector = _coerce_sector(row.get("own_sector"))
    c = _safe_float(own_sector.get("critical"), default=0.0)
    total_alloc = c + float(action.amount)
    rf = _piecewise_revenue_factor_for_amount(total_alloc, own_sector)
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

    c = _safe_float(target.get("critical"), default=0.0)
    disc = _safe_float(proposal.get("amount"), default=0.0)
    total_alloc = c + disc
    rf = _piecewise_revenue_factor_for_amount(total_alloc, target)

    if action.vote is VoteChoice.YES:
        return VOTE_YES_WEIGHT * (rf - 1.0)
    if action.vote is VoteChoice.NO:
        return VOTE_NO_WEIGHT * (-(rf - 1.0))
    return VOTE_NEUTRAL_REWARD


def _piecewise_revenue_factor_for_amount(
    amount: float,
    sector: Mapping[str, float],
) -> float:
    """Wrap :func:`core.revenue.revenue_factor`, treating critical-failure as 0.0."""
    critical = float(sector["critical"])
    demand = float(sector["demand"])
    surplus = float(sector["surplus"])
    wastage = float(sector["wastage"]) if "wastage" in sector else demand * WASTAGE_RATIO
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
    return value  # "wastage" optional; RF uses demand*WASTAGE_RATIO if absent


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
    "ILLEGAL_ACTION_REWARD",
    "PARSE_FAIL_REWARD",
    "PROPOSE_BASE_REWARD",
    "PROPOSE_FACTOR_WEIGHT",
    "SURVIVAL_SHAPING_WEIGHT",
    "VOTE_NEUTRAL_REWARD",
    "VOTE_NO_WEIGHT",
    "VOTE_YES_WEIGHT",
    "make_reward_fn",
]
