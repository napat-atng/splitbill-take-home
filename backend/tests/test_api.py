from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func
from sqlmodel import Session, delete, select

from app.core.database import get_session
from app.main import app
from app.models import Expense, ExpenseShare
from app.repositories import expenses as expense_repository

pytestmark = pytest.mark.database


@pytest.fixture
def client(database: tuple[Engine, Config]) -> Iterator[TestClient]:
    engine = database[0]
    with Session(engine) as session, session.begin():
        session.exec(delete(ExpenseShare))
        session.exec(delete(Expense))

    def test_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)


def payload(**changes) -> dict:
    return {
        "description": "Dinner",
        "paid_by": "alice",
        "amount": "100.00",
        "split": {"type": "equal", "members": ["alice", "bob", "carol"]},
    } | changes


def create(client: TestClient, *, user="alice", group=1, key="dinner", data=None):
    return client.post(
        f"/groups/{group}/expenses",
        headers={"X-User": user, "Idempotency-Key": key},
        json=payload() if data is None else data,
    )


def test_groups_and_zero_balances(client: TestClient) -> None:
    assert [g["id"] for g in client.get("/groups", headers={"X-User": "alice"}).json()] == [1]
    assert [g["id"] for g in client.get("/groups", headers={"X-User": "bob"}).json()] == [1, 2]
    assert client.get("/groups/1", headers={"X-User": "carol"}).json()["members"] == [
        "alice",
        "bob",
        "carol",
    ]
    assert client.get("/groups/1/balances", headers={"X-User": "alice"}).json() == {
        "group_id": 1,
        "balances": {"alice": "0.00", "bob": "0.00", "carol": "0.00"},
    }


def test_equal_allocation_and_zero_sum(client: TestClient) -> None:
    response = create(client)
    assert response.status_code == 201
    record = response.json()
    assert record["amount"] == "100.00"
    assert record["split"]["shares"] == {"alice": "33.34", "bob": "33.33", "carol": "33.33"}
    balances = client.get("/groups/1/balances", headers={"X-User": "alice"}).json()["balances"]
    assert balances == {"alice": "66.66", "bob": "-33.33", "carol": "-33.33"}
    assert sum(map(Decimal, balances.values())) == Decimal("0.00")


def test_brief_example_and_order(client: TestClient) -> None:
    first = create(client, data=payload(amount="1000.00")).json()
    assert first["split"]["shares"] == {"alice": "333.34", "bob": "333.33", "carol": "333.33"}
    balances = client.get("/groups/1/balances", headers={"X-User": "alice"}).json()["balances"]
    assert balances == {"alice": "666.66", "bob": "-333.33", "carol": "-333.33"}
    second = create(
        client,
        key="ordered",
        data=payload(amount="0.01", split={"type": "equal", "members": ["carol", "alice", "bob"]}),
    ).json()
    assert list(second["split"]["shares"].items()) == [
        ("carol", "0.01"),
        ("alice", "0.00"),
        ("bob", "0.00"),
    ]
    records = client.get("/groups/1/expenses", headers={"X-User": "bob"}).json()
    assert [r["id"] for r in records] == [second["id"], first["id"]]


def test_exact_split_and_payer_not_in_split(client: TestClient) -> None:
    response = create(
        client,
        user="bob",
        data=payload(split={"type": "exact", "shares": {"bob": "100.00", "carol": "0.00"}}),
    )
    assert response.status_code == 201
    balances = client.get("/groups/1/balances", headers={"X-User": "alice"}).json()["balances"]
    assert balances == {"alice": "100.00", "bob": "-100.00", "carol": "0.00"}


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "10.005"},
        {"amount": "0.00"},
        {"amount": "-1.00"},
        {"amount": 100.0},
        {"amount": "10000000000.00"},
        {"amount": "NaN"},
        {"amount": "1e2"},
        {"split": {"type": "exact", "shares": {"alice": "99.99"}}},
        {"split": {"type": "exact", "shares": {"alice": "100.005"}}},
        {"split": {"type": "exact", "shares": {"alice": "101", "bob": "-1"}}},
        {"split": {"type": "equal", "members": []}},
        {"split": {"type": "equal", "members": ["alice", "alice"]}},
        {"split": {"type": "exact", "shares": {}}},
        {"split": {"type": "equal", "members": ["alice", "dan"]}},
        {"split": {"type": "exact", "shares": {"dan": "100"}}},
        {"paid_by": "dan"},
        {"description": " "},
    ],
)
def test_invalid_expenses_rejected(client: TestClient, changes: dict) -> None:
    response = create(client, data=payload(**changes))
    assert response.status_code == 422
    assert set(response.json()["error"]) == {"code", "message", "details"}
    assert client.get("/groups/1/expenses", headers={"X-User": "alice"}).json() == []


def test_exact_mismatch_is_descriptive(client: TestClient) -> None:
    response = create(client, data=payload(split={"type": "exact", "shares": {"alice": "99"}}))
    assert response.json()["error"]["message"] == "The shares do not add up to the total"


def test_idempotency_replays_first_payload(
    client: TestClient, database: tuple[Engine, Config]
) -> None:
    first = create(client)
    second = create(client, data=payload(description="Changed", amount="200.00"))
    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json() == second.json()
    with Session(database[0]) as session:
        assert session.exec(select(func.count()).select_from(Expense)).one() == 1
        assert session.exec(select(func.count()).select_from(ExpenseShare)).one() == 3


def test_concurrent_idempotency_returns_same_expense(
    client: TestClient,
    database: tuple[Engine, Config],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    barrier = Barrier(4)
    original = expense_repository.create_expense

    def simultaneous_insert(*args, **kwargs):
        barrier.wait(timeout=15)
        return original(*args, **kwargs)

    monkeypatch.setattr(expense_repository, "create_expense", simultaneous_insert)
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda _: create(client), range(4)))
    assert sorted(r.status_code for r in responses) == [200, 200, 200, 201]
    assert all(r.json() == responses[0].json() for r in responses)
    with Session(database[0]) as session:
        assert session.exec(select(func.count()).select_from(Expense)).one() == 1
        assert session.exec(select(func.count()).select_from(ExpenseShare)).one() == 3


@pytest.mark.parametrize("path", ["/groups/2", "/groups/2/expenses", "/groups/2/balances"])
def test_non_member_cannot_read(client: TestClient, path: str) -> None:
    response = client.get(path, headers={"X-User": "alice"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_group_member"


def test_non_member_cannot_write_or_replay(client: TestClient) -> None:
    response = create(
        client,
        group=2,
        user="bob",
        data=payload(paid_by="bob", split={"type": "equal", "members": ["bob", "dan"]}),
    )
    assert response.status_code == 201
    assert create(client, group=2).status_code == 403
    assert (
        client.delete(
            f"/groups/2/expenses/{response.json()['id']}", headers={"X-User": "alice"}
        ).status_code
        == 403
    )
    assert create(client).status_code == 201  # same key, different group is independent


def test_soft_delete_and_replay(client: TestClient, database: tuple[Engine, Config]) -> None:
    record = create(client).json()
    path = f"/groups/1/expenses/{record['id']}"
    assert client.delete(path, headers={"X-User": "bob"}).status_code == 403
    assert client.delete(path, headers={"X-User": "alice"}).status_code == 204
    assert client.delete(path, headers={"X-User": "alice"}).status_code == 204
    assert client.get("/groups/1/expenses", headers={"X-User": "alice"}).json() == []
    balances = client.get("/groups/1/balances", headers={"X-User": "alice"}).json()["balances"]
    assert set(balances.values()) == {"0.00"}
    replay = create(client)
    assert replay.status_code == 200
    assert replay.json()["id"] == record["id"]
    assert replay.json()["is_deleted"] is True
    with Session(database[0]) as session:
        assert session.get(Expense, record["id"]).is_deleted is True
        assert len(session.exec(select(ExpenseShare)).all()) == 3


def test_expense_group_must_match_delete_path(client: TestClient) -> None:
    record = create(
        client,
        group=2,
        user="bob",
        data=payload(paid_by="bob", split={"type": "equal", "members": ["bob", "dan"]}),
    ).json()
    response = client.delete(f"/groups/1/expenses/{record['id']}", headers={"X-User": "bob"})
    assert response.status_code == 404


@pytest.mark.parametrize("headers", [{}, {"X-User": "unknown"}])
def test_unknown_user(client: TestClient, headers: dict) -> None:
    response = client.get("/groups", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unknown_user"


def test_missing_key_and_no_edit_endpoint(client: TestClient) -> None:
    response = client.post("/groups/1/expenses", headers={"X-User": "alice"}, json=payload())
    assert response.status_code == 422
    record = create(client).json()
    assert (
        client.patch(
            f"/groups/1/expenses/{record['id']}", headers={"X-User": "alice"}, json={"amount": "1"}
        ).status_code
        == 405
    )
    assert client.get("/groups/999", headers={"X-User": "alice"}).status_code == 404


def test_decimal_addition_is_exact(client: TestClient) -> None:
    for amount in ("0.10", "0.20"):
        assert (
            create(
                client,
                key=amount,
                data=payload(amount=amount, split={"type": "exact", "shares": {"bob": amount}}),
            ).status_code
            == 201
        )
    assert client.get("/groups/1/balances", headers={"X-User": "alice"}).json()["balances"] == {
        "alice": "0.30",
        "bob": "-0.30",
        "carol": "0.00",
    }
