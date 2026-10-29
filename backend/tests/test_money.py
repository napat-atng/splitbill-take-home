from decimal import Decimal

import pytest

from app.services.money import calculate_balances, parse_amount, split_equal, split_exact


def test_equal_split_preserves_amount_and_member_order() -> None:
    shares = split_equal("100.00", ["carol", "bob", "alice"])
    assert list(shares.values()) == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(shares.values()) == Decimal("100.00")


def test_amount_smaller_than_member_count() -> None:
    assert list(split_equal("0.01", ["alice", "bob"]).values()) == [
        Decimal("0.01"),
        Decimal("0.00"),
    ]


@pytest.mark.parametrize("value", ["10.005", "0", "-1", "NaN", "Infinity", "10000000000"])
def test_invalid_amounts(value: str) -> None:
    with pytest.raises(ValueError):
        parse_amount(value)


@pytest.mark.parametrize("members", [[], ["alice", "alice"]])
def test_invalid_member_selection(members: list[str]) -> None:
    with pytest.raises(ValueError):
        split_equal("100.00", members)


def test_exact_allocation() -> None:
    assert split_exact("100.00", {"alice": "75.00", "bob": "25.00", "carol": "0.00"}) == {
        "alice": Decimal("75.00"),
        "bob": Decimal("25.00"),
        "carol": Decimal("0.00"),
    }


@pytest.mark.parametrize(
    "shares", [{}, {"alice": "99.99"}, {"alice": "100.005"}, {"alice": "101", "bob": "-1"}]
)
def test_exact_allocation_rejects_invalid_shares(shares: dict[str, str]) -> None:
    with pytest.raises(ValueError):
        split_exact("100.00", shares)


def test_balances_include_members_without_expenses() -> None:
    assert calculate_balances(
        ["alice", "bob", "carol"], {"alice": Decimal("0.30"), "bob": Decimal("-0.30")}
    ) == {"alice": Decimal("0.30"), "bob": Decimal("-0.30"), "carol": Decimal("0.00")}


def test_balances_detect_non_zero_sum() -> None:
    with pytest.raises(ValueError):
        calculate_balances(["alice", "bob"], {"alice": Decimal("0.01")})
