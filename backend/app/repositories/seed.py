"""Idempotent insertion of the fixed take-home dataset."""

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models import Group, Membership, User

USERS = ("alice", "bob", "carol", "dan")
GROUPS = ((1, "Chiang Mai trip"), (2, "Office lunch"))
MEMBERSHIPS = ((1, "alice"), (1, "bob"), (1, "carol"), (2, "bob"), (2, "dan"))


def seed_data(session: Session) -> None:
    """Run inside the caller's transaction; preserve all existing application data."""
    session.exec(text("SELECT pg_advisory_xact_lock(74219301)"))
    for username in USERS:
        session.execute(insert(User).values(username=username).on_conflict_do_nothing())
    for group_id, name in GROUPS:
        session.execute(insert(Group).values(id=group_id, name=name).on_conflict_do_nothing())
        if session.get(Group, group_id).name != name:
            raise ValueError(f"Seed group {group_id} conflicts with an existing group")
    for group_id, username in MEMBERSHIPS:
        session.execute(
            insert(Membership).values(group_id=group_id, username=username).on_conflict_do_nothing()
        )
    # Explicit seed IDs must not collide with the next generated group ID.
    # Only advance an unused sequence; never move it behind its current value.
    max_id = session.exec(select(func.max(Group.id))).one()
    session.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('groups', 'id'), "
            "GREATEST(:max_id, (SELECT last_value FROM groups_id_seq)), true)"
        ),
        {"max_id": max_id},
    )
