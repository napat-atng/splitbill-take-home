import re
from decimal import Decimal

SATANG = Decimal("0.01")
MAX_AMOUNT = Decimal("9999999999.99")


def parse_money(value: str, *, allow_zero: bool = False) -> Decimal:
    """Accept plain decimal strings only; never round invalid input."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", value):
        raise ValueError("Money must be a decimal string with at most 2 decimal places")
    # Bound the significant integer digits before Decimal arithmetic.
    if len(value.split(".")[0].lstrip("0")) > 10:
        raise ValueError("Amount exceeds NUMERIC(12,2)")
    amount = Decimal(value)
    if amount > MAX_AMOUNT or (amount == 0 and not allow_zero):
        raise ValueError("Amount must be positive and fit NUMERIC(12,2)")
    return amount.quantize(SATANG)


def parse_amount(value: str) -> Decimal:
    return parse_money(value)


def split_equal(amount: str, members: list[str]) -> dict[str, Decimal]:
    """Allocate remaining satang in request order, independently of HTTP/database."""
    total = parse_amount(amount)
    if not members or len(set(members)) != len(members):
        raise ValueError("Select unique members")
    share, remainder = divmod(int(total * 100), len(members))
    return {
        member: (Decimal(share + (index < remainder)) / 100).quantize(SATANG)
        for index, member in enumerate(members)
    }


def split_exact(amount: str, shares: dict[str, str]) -> dict[str, Decimal]:
    total = parse_amount(amount)
    if not shares:
        raise ValueError("Select at least one member")
    parsed = {member: parse_money(share, allow_zero=True) for member, share in shares.items()}
    if sum(parsed.values(), Decimal("0.00")) != total:
        raise ValueError("The shares do not add up to the total")
    return parsed


def calculate_balances(members: list[str], ledger: dict[str, Decimal]) -> dict[str, Decimal]:
    balances = {member: ledger.get(member, Decimal("0.00")).quantize(SATANG) for member in members}
    if set(ledger) - set(members) or sum(balances.values(), Decimal("0.00")) != 0:
        raise ValueError("Group balances must sum to 0.00")
    return balances
