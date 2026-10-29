from sqlmodel import Session

from app.core.errors import AppError
from app.models import Expense
from app.repositories import expenses, groups
from app.schemas import BalancesRead, EqualSplit, ExpenseCreate, ExpenseRead, SplitRead
from app.services.money import calculate_balances, parse_amount, split_equal, split_exact


def read_expenses(session: Session, records: list[Expense]) -> list[ExpenseRead]:
    shares = expenses.get_shares(session, [record.id for record in records])
    return [
        ExpenseRead(
            id=record.id,
            group_id=record.group_id,
            description=record.description,
            paid_by=record.paid_by,
            amount=format(record.amount, ".2f"),
            split=SplitRead(
                type=record.split_type,
                shares={
                    member: format(amount, ".2f") for member, amount in shares[record.id].items()
                },
            ),
            created_at=record.created_at,
            is_deleted=record.is_deleted,
        )
        for record in records
    ]


def create_expense(
    session: Session,
    group_id: int,
    key: str,
    payload: ExpenseCreate,
) -> tuple[ExpenseRead, bool]:
    existing = expenses.get_by_key(session, group_id, key)
    if existing is not None:
        return read_expenses(session, [existing])[0], False
    members = groups.get_members(session, group_id)
    try:
        amount = parse_amount(payload.amount)
        if isinstance(payload.split, EqualSplit):
            shares = split_equal(payload.amount, payload.split.members)
        else:
            shares = split_exact(payload.amount, payload.split.shares)
    except ValueError as exc:
        raise AppError(422, "invalid_split", str(exc)) from exc
    if payload.paid_by not in members or not set(shares).issubset(members):
        raise AppError(
            422, "invalid_member", "The payer and split members must belong to this group"
        )
    record, created = expenses.create_expense(
        session,
        group_id=group_id,
        description=payload.description,
        paid_by=payload.paid_by,
        amount=amount,
        split_type=payload.split.type,
        key=key,
        shares=shares,
    )
    session.commit()
    return read_expenses(session, [record])[0], created


def delete_expense(session: Session, group_id: int, expense_id: int, user: str) -> None:
    record = expenses.get_expense(session, group_id, expense_id)
    if record is None:
        raise AppError(404, "expense_not_found", "Expense not found in this group")
    if record.paid_by != user:
        raise AppError(403, "payer_only", "Only the payer can delete this expense")
    record.is_deleted = True
    session.add(record)
    session.commit()


def get_balances(session: Session, group_id: int) -> BalancesRead:
    members = groups.get_members(session, group_id)
    ledger = expenses.get_totals(session, group_id)
    try:
        balances = calculate_balances(members, ledger)
    except ValueError as exc:
        raise AppError(
            500, "invalid_balances", "Stored expense allocations are inconsistent"
        ) from exc
    return BalancesRead(
        group_id=group_id,
        balances={member: format(amount, ".2f") for member, amount in balances.items()},
    )
