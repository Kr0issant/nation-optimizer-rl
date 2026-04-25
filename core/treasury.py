"""
treasury.py — Central treasury bookkeeping.

Simple debit/credit ledger.  The game orchestrator handles sequencing
(debit allocations → credit revenue → credit surplus → baseline tax).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Treasury:
    """Mutable treasury state."""

    balance: float
    baseline_tax: float = 100.0
    history: list[float] = field(default_factory=list, repr=False)

    # ── Operations ──────────────────────────────────────────────
    def debit(self, amount: float) -> None:
        """Subtract *amount* from balance (e.g. budget allocation)."""
        self.balance -= amount

    def credit(self, amount: float) -> None:
        """Add *amount* to balance (e.g. revenue, surplus return)."""
        self.balance += amount

    def apply_baseline_tax(self) -> None:
        """Credit the per-round baseline tax income."""
        self.credit(self.baseline_tax)

    # ── Queries ─────────────────────────────────────────────────
    def is_bankrupt(self) -> bool:
        """True when the nation can no longer operate."""
        return self.balance <= 0

    def can_afford(self, total_allocation: float) -> bool:
        """True when balance covers the requested total allocation."""
        return self.balance >= total_allocation

    # ── Snapshot ────────────────────────────────────────────────
    def snapshot(self) -> None:
        """Record current balance for history tracking."""
        self.history.append(self.balance)
