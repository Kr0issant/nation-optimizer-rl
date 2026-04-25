import pytest

from core.config import BASELINE_TAX
from core.treasury import Treasury


def test_baseline_tax_credits_balance() -> None:
    treasury = Treasury(balance=100)

    treasury.apply_baseline_tax()

    assert treasury.balance == 100 + BASELINE_TAX


def test_debit_reduces_balance() -> None:
    treasury = Treasury(balance=100)

    treasury.debit(40)

    assert treasury.balance == 60


def test_credit_increases_balance() -> None:
    treasury = Treasury(balance=100)

    treasury.credit(40)

    assert treasury.balance == 140


def test_overdraft_raises_value_error() -> None:
    treasury = Treasury(balance=100)

    with pytest.raises(ValueError):
        treasury.debit(101)


def test_negative_debit_and_credit_raise_value_error() -> None:
    treasury = Treasury(balance=100)

    with pytest.raises(ValueError):
        treasury.debit(-1)
    with pytest.raises(ValueError):
        treasury.credit(-1)


def test_bankruptcy_detects_balance_less_than_or_equal_to_zero() -> None:
    assert Treasury(balance=0).is_bankrupt()
    assert Treasury(balance=-1).is_bankrupt()
    assert not Treasury(balance=1).is_bankrupt()
