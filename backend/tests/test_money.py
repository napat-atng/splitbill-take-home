from decimal import Decimal

import pytest

from app.services.money import parse_amount, split_equal


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
