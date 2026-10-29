from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models import Expense, ExpenseShare


def get_by_key(session: Session, group_id: int, key: str) -> Expense | None:
    return session.exec(
        select(Expense).where(Expense.group_id == group_id, Expense.idempotency_key == key)
    ).first()


def get_expense(session: Session, group_id: int, expense_id: int) -> Expense | None:
    return session.exec(
        select(Expense).where(Expense.group_id == group_id, Expense.id == expense_id)
    ).first()


def list_expenses(session: Session, group_id: int) -> list[Expense]:
    return list(
        session.exec(
            select(Expense)
            .where(Expense.group_id == group_id, Expense.is_deleted.is_(False))
            .order_by(Expense.created_at.desc(), Expense.id.desc())
        ).all()
    )


def get_shares(session: Session, expense_ids: list[int]) -> dict[int, dict[str, Decimal]]:
    if not expense_ids:
        return {}
    rows = session.exec(
        select(ExpenseShare)
        .where(ExpenseShare.expense_id.in_(expense_ids))
        .order_by(ExpenseShare.expense_id, ExpenseShare.position)
    ).all()
    result: dict[int, dict[str, Decimal]] = {}
    for row in rows:
        result.setdefault(row.expense_id, {})[row.username] = row.amount
    return result


def create_expense(
    session: Session,
    *,
    group_id: int,
    description: str,
    paid_by: str,
    amount: Decimal,
    split_type: str,
    key: str,
    shares: dict[str, Decimal],
) -> tuple[Expense, bool]:
    statement = (
        insert(Expense)
        .values(
            group_id=group_id,
            description=description,
            paid_by=paid_by,
            amount=amount,
            split_type=split_type,
            idempotency_key=key,
        )
        .on_conflict_do_nothing(constraint="uq_expenses_group_key")
        .returning(Expense)
    )
    record = session.execute(statement).scalars().first()
    if record is None:
        # READ COMMITTED: this new SELECT sees the competing transaction's committed row.
        return get_by_key(session, group_id, key), False
    session.add_all(
        [
            ExpenseShare(
                expense_id=record.id,
                group_id=group_id,
                username=username,
                amount=share,
                position=position,
            )
            for position, (username, share) in enumerate(shares.items())
        ]
    )
    session.flush()
    return record, True


def get_totals(session: Session, group_id: int) -> dict[str, Decimal]:
    # One statement/snapshot for both sides, even while other requests insert/delete expenses.
    paid = select(Expense.paid_by.label("member"), Expense.amount.label("value")).where(
        Expense.group_id == group_id, Expense.is_deleted.is_(False)
    )
    owed = (
        select(ExpenseShare.username.label("member"), (-ExpenseShare.amount).label("value"))
        .join(Expense, Expense.id == ExpenseShare.expense_id)
        .where(Expense.group_id == group_id, Expense.is_deleted.is_(False))
    )
    ledger = paid.union_all(owed).subquery()
    totals = session.execute(
        select(ledger.c.member, func.sum(ledger.c.value)).group_by(ledger.c.member)
    ).all()
    return dict(totals)
