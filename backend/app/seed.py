"""Run `uv run python -m app.seed` after `uv run alembic upgrade head`."""

from sqlmodel import Session

from app.core.database import get_engine
from app.repositories.seed import seed_data


def main() -> None:
    with Session(get_engine()) as session, session.begin():
        seed_data(session)
    print("Seed complete: alice, bob, carol, dan; 2 groups; 5 memberships")


if __name__ == "__main__":
    main()
