"""
treasury.py — Central treasury bookkeeping.

Simple debit/credit ledger.  The game orchestrator handles sequencing
(debit allocations → credit revenue → credit surplus → baseline tax).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import BASELINE_TAX, INITIAL_TREASURY


@dataclass
class Treasury:
    """Mutable treasury state."""

    balance: float = float(INITIAL_TREASURY)
    baseline_tax: float = float(BASELINE_TAX)
    history: list[float] = field(default_factory=list, repr=False)

    # ── Operations ──────────────────────────────────────────────
    def debit(self, amount: float) -> None:
        """Subtract *amount* from balance (e.g. budget allocation)."""
        if amount < 0:
            raise ValueError("debit amount cannot be negative")
        if amount > self.balance:
            raise ValueError("cannot debit more than the current balance")
        self.balance -= amount

    def credit(self, amount: float) -> None:
        """Add *amount* to balance (e.g. revenue, surplus return)."""
        if amount < 0:
            raise ValueError("credit amount cannot be negative")
        self.balance += amount

    def apply_baseline_tax(self) -> None:
        """Credit the per-round baseline tax income."""
        self.credit(self.baseline_tax)

    # ── Queries ─────────────────────────────────────────────────
    def is_bankrupt(self) -> bool:
        """True when the nation can no longer operate."""
        return self.balance <= 0

    def can_debit(self, amount: float) -> bool:
        """True when balance covers a non-negative debit amount."""
        return amount >= 0 and self.balance >= amount

    def can_afford(self, total_allocation: float) -> bool:
        """True when balance covers the requested total allocation."""
        return self.can_debit(total_allocation)

    # ── Snapshot ────────────────────────────────────────────────
    def snapshot(self) -> None:
        """Record current balance for history tracking."""
        self.history.append(self.balance)
