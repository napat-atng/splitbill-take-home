"""Integration tests use a new database, never the configured application's tables."""

import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine

from app.core.config import get_settings
from app.repositories.seed import seed_data


@pytest.fixture(scope="module")
def database() -> Iterator[tuple[Engine, Config]]:
    if os.environ.get("RUN_DB_TESTS") == "0":
        pytest.skip("RUN_DB_TESTS=0 disables PostgreSQL integration tests")
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
