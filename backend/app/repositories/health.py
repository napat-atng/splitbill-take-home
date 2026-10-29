from sqlalchemy import text
from sqlmodel import Session


def check_connection(session: Session) -> None:
    session.exec(text("SELECT 1")).one()
