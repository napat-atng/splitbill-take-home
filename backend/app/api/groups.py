from typing import Annotated

from fastapi import APIRouter, Header, Path, Response

from app.api.dependencies import CurrentUserDep, GroupAccessDep
from app.core.database import SessionDep
from app.repositories import expenses as expense_repository
from app.repositories import groups as group_repository
from app.schemas import (
    BalancesRead,
    ErrorRead,
    ExpenseCreate,
    ExpenseRead,
    GroupDetail,
    GroupSummary,
)
from app.services import expenses as expense_service

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
    responses={status: {"model": ErrorRead} for status in (401, 403, 404, 422, 503)},
)
IdempotencyKey = Annotated[
    str, Header(alias="Idempotency-Key", min_length=1, max_length=255, pattern=r".*\S.*")
]
ExpenseId = Annotated[int, Path(gt=0)]


@router.get("")
def list_groups(user: CurrentUserDep, session: SessionDep) -> list[GroupSummary]:
    return [
        GroupSummary(id=group.id, name=group.name)
        for group in group_repository.list_groups(session, user)
    ]


@router.get("/{group_id}")
def get_group(group: GroupAccessDep, session: SessionDep) -> GroupDetail:
    return GroupDetail(
        id=group.id, name=group.name, members=group_repository.get_members(session, group.id)
    )


@router.post("/{group_id}/expenses", status_code=201, responses={200: {"model": ExpenseRead}})
def create_expense(
    payload: ExpenseCreate,
    group: GroupAccessDep,
    session: SessionDep,
    response: Response,
    key: IdempotencyKey,
) -> ExpenseRead:
    record, created = expense_service.create_expense(session, group.id, key, payload)
    response.status_code = 201 if created else 200
    return record


@router.get("/{group_id}/expenses")
def list_expenses(group: GroupAccessDep, session: SessionDep) -> list[ExpenseRead]:
    records = expense_repository.list_expenses(session, group.id)
    return expense_service.read_expenses(session, records)


@router.delete("/{group_id}/expenses/{expense_id}", status_code=204)
def delete_expense(
    expense_id: ExpenseId,
    group: GroupAccessDep,
    user: CurrentUserDep,
    session: SessionDep,
) -> Response:
    expense_service.delete_expense(session, group.id, expense_id, user)
    return Response(status_code=204)


@router.get("/{group_id}/balances")
def get_balances(group: GroupAccessDep, session: SessionDep) -> BalancesRead:
    return expense_service.get_balances(session, group.id)
