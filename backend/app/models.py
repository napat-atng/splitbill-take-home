"""Persistence models. HTTP schemas will be separate from these tables."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    username: str = Field(primary_key=True, max_length=64)


class Group(SQLModel, table=True):
    __tablename__ = "groups"
    id: int | None = Field(default=None, sa_column=Column(Integer, Identity(), primary_key=True))
    name: str = Field(max_length=200)


class Membership(SQLModel, table=True):
    __tablename__ = "memberships"
    __table_args__ = (Index("ix_memberships_username", "username"),)
    group_id: int = Field(foreign_key="groups.id", primary_key=True)
    username: str = Field(foreign_key="users.username", primary_key=True, max_length=64)


class Expense(SQLModel, table=True):
    __tablename__ = "expenses"
    __table_args__ = (
        ForeignKeyConstraint(
            ["group_id", "paid_by"],
            ["memberships.group_id", "memberships.username"],
            name="fk_expenses_payer_membership",
        ),
        UniqueConstraint("group_id", "idempotency_key", name="uq_expenses_group_key"),
        UniqueConstraint("id", "group_id", name="uq_expenses_id_group"),
        CheckConstraint("amount > 0 AND amount <= 9999999999.99", name="ck_expenses_amount"),
        CheckConstraint("split_type IN ('equal', 'exact')", name="ck_expenses_split_type"),
        CheckConstraint("length(trim(description)) > 0", name="ck_expenses_description"),
        CheckConstraint("length(trim(idempotency_key)) > 0", name="ck_expenses_key"),
        Index("ix_expenses_group_created_id", "group_id", "created_at", "id"),
    )
    id: int | None = Field(default=None, sa_column=Column(Integer, Identity(), primary_key=True))
    group_id: int = Field(foreign_key="groups.id")
    description: str = Field(max_length=500)
    paid_by: str = Field(max_length=64)
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    split_type: str = Field(max_length=5)
    idempotency_key: str = Field(max_length=255)
    is_deleted: bool = Field(default=False, sa_column_kwargs={"server_default": text("false")})
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


class ExpenseShare(SQLModel, table=True):
    __tablename__ = "expense_shares"
    __table_args__ = (
        ForeignKeyConstraint(
            ["expense_id", "group_id"],
            ["expenses.id", "expenses.group_id"],
            name="fk_shares_expense_group",
        ),
        ForeignKeyConstraint(
            ["group_id", "username"],
            ["memberships.group_id", "memberships.username"],
            name="fk_shares_membership",
        ),
        UniqueConstraint("expense_id", "position", name="uq_shares_expense_position"),
        CheckConstraint("amount >= 0 AND amount <= 9999999999.99", name="ck_shares_amount"),
        CheckConstraint("position >= 0", name="ck_shares_position"),
        Index("ix_shares_group_username", "group_id", "username"),
    )
    expense_id: int = Field(primary_key=True)
    username: str = Field(primary_key=True, max_length=64)
    group_id: int
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    position: int
