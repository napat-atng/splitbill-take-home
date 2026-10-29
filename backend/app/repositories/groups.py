from sqlmodel import Session, select

from app.models import Group, Membership, User


def get_user(session: Session, username: str) -> User | None:
    return session.get(User, username)


def get_group(session: Session, group_id: int) -> Group | None:
    return session.get(Group, group_id)


def get_members(session: Session, group_id: int) -> list[str]:
    return list(
        session.exec(
            select(Membership.username)
            .where(Membership.group_id == group_id)
            .order_by(Membership.username)
        ).all()
    )


def list_groups(session: Session, username: str) -> list[Group]:
    return list(
        session.exec(
            select(Group).join(Membership).where(Membership.username == username).order_by(Group.id)
        ).all()
    )
