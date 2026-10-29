from typing import Annotated

from fastapi import Depends, Header, Path

from app.core.database import SessionDep
from app.core.errors import AppError
from app.models import Group
from app.repositories import groups

GroupId = Annotated[int, Path(gt=0)]


def current_user(
    session: SessionDep,
    x_user: Annotated[str | None, Header(max_length=64)] = None,
) -> str:
    if not x_user or groups.get_user(session, x_user) is None:
        raise AppError(401, "unknown_user", "A valid X-User header is required")
    return x_user


CurrentUserDep = Annotated[str, Depends(current_user)]


def group_access(group_id: GroupId, user: CurrentUserDep, session: SessionDep) -> Group:
    group = groups.get_group(session, group_id)
    if group is None:
        raise AppError(404, "group_not_found", "Group not found")
    if user not in groups.get_members(session, group_id):
        raise AppError(403, "not_group_member", "Not a member of this group")
    return group


GroupAccessDep = Annotated[Group, Depends(group_access)]
