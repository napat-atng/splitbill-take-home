"""Opt-in PostgreSQL tests, always isolated in a newly created temporary database."""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine, select

from app.core.config import get_settings
from app.models import Expense, ExpenseShare, Group, Membership, User
from app.repositories.seed import seed_data

pytestmark = pytest.mark.database


@pytest.fixture(scope="module")
def database() -> Iterator[tuple[Engine, Config]]:
    if os.environ.get("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to run isolated PostgreSQL migration/seed tests")
    original_url = make_url(get_settings().database_url)
    name = "splitbill_test_" + uuid4().hex
    admin = create_engine(
        original_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 3},
    )
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    test_url = original_url.set(database=name)
    engine = create_engine(test_url, connect_args={"connect_timeout": 3})
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv("DATABASE_URL", test_url.render_as_string(hide_password=False))
            get_settings.cache_clear()
            command.upgrade(config, "head")
            command.upgrade(config, "head")
            with Session(engine) as session, session.begin():
                seed_data(session)
            yield engine, config
    finally:
        get_settings.cache_clear()
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def session(database: tuple[Engine, Config]) -> Iterator[Session]:
    with Session(database[0]) as session:
        yield session
        session.rollback()


def expense(**changes) -> Expense:
    values = dict(
        group_id=1,
        description="Dinner",
        paid_by="alice",
        amount=Decimal("100.00"),
        split_type="equal",
        idempotency_key="test-key",
    )
    return Expense(**(values | changes))


def test_seed_twice_is_exact_and_preserves_expenses(session: Session) -> None:
    record = expense()
    session.add(record)
    session.flush()
    seed_data(session)
    seed_data(session)
    assert set(session.exec(select(User.username)).all()) == {"alice", "bob", "carol", "dan"}
    assert {(g.id, g.name) for g in session.exec(select(Group)).all()} == {
        (1, "Chiang Mai trip"),
        (2, "Office lunch"),
    }
    assert {(m.group_id, m.username) for m in session.exec(select(Membership)).all()} == {
        (1, "alice"),
        (1, "bob"),
        (1, "carol"),
        (2, "bob"),
        (2, "dan"),
    }
    assert session.get(Expense, record.id).amount == Decimal("100.00")
    group = Group(name="New group")
    session.add(group)
    session.flush()
    assert group.id > 2


def test_schema_money_and_soft_delete(session: Session, database: tuple[Engine, Config]) -> None:
    for table in ("expenses", "expense_shares"):
        column = next(c for c in inspect(database[0]).get_columns(table) if c["name"] == "amount")
        assert (column["type"].precision, column["type"].scale) == (12, 2)
    record = expense()
    session.add(record)
    session.flush()
    session.refresh(record)
    assert record.is_deleted is False
    assert record.created_at.tzinfo is not None
    record.is_deleted = True
    session.add(record)
    session.flush()
    assert session.get(Expense, record.id).is_deleted is True


@pytest.mark.parametrize(
    "changes",
    [
        {"paid_by": "dan"},
        {"group_id": 2},
        {"amount": Decimal("0")},
        {"amount": Decimal("-0.01")},
        {"amount": Decimal("NaN")},
        {"split_type": "other"},
        {"description": " "},
        {"idempotency_key": " "},
    ],
)
def test_expense_constraints(session: Session, changes: dict) -> None:
    session.add(expense(**changes))
    with pytest.raises(IntegrityError):
        session.flush()


def test_key_unique_per_group(session: Session) -> None:
    session.add(expense())
    session.add(expense(group_id=2, paid_by="bob"))
    session.flush()
    session.add(expense())
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize(
    "changes",
    [
        {"username": "dan"},
        {"group_id": 2},
        {"amount": Decimal("-0.01")},
        {"position": -1},
    ],
)
def test_share_constraints(session: Session, changes: dict) -> None:
    record = expense()
    session.add(record)
    session.flush()
    values = dict(
        expense_id=record.id, group_id=1, username="alice", amount=Decimal("100"), position=0
    )
    session.add(ExpenseShare(**(values | changes)))
    with pytest.raises(IntegrityError):
        session.flush()


def test_concurrent_key_uniqueness(database: tuple[Engine, Config]) -> None:
    barrier = Barrier(2)

    def insert_expense() -> bool:
        try:
            with Session(database[0]) as session, session.begin():
                session.add(expense(idempotency_key="concurrent-key"))
                barrier.wait(timeout=10)
            return True
        except IntegrityError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: insert_expense(), range(2)))
    assert sorted(results) == [False, True]


def test_migration_round_trip(database: tuple[Engine, Config]) -> None:
    engine, config = database
    command.check(config)
    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    command.upgrade(config, "head")
    command.check(config)
    with Session(engine) as session, session.begin():
        seed_data(session)
