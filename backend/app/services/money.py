from decimal import Decimal, InvalidOperation

SATANG = Decimal("0.01")
MAX_AMOUNT = Decimal("9999999999.99")


def parse_amount(value: str) -> Decimal:
    """Parse a positive expense amount without rounding user input."""
    if not isinstance(value, str):
        raise ValueError("Amount must be a decimal string")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid amount") from exc
    if not amount.is_finite() or amount <= 0 or amount > MAX_AMOUNT:
        raise ValueError("Amount must be positive and fit NUMERIC(12,2)")
    if amount.as_tuple().exponent < -2:
        raise ValueError("Amount must have at most 2 decimal places")
    return amount.quantize(SATANG)


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
