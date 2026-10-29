"""Run frontend browser tests against a disposable PostgreSQL database.

From backend/: uv run python -m scripts.test_frontend
Extra arguments are passed to Playwright, e.g. --project=desktop.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool
from sqlmodel import Session, create_engine

from app.core.config import get_settings
from app.repositories.seed import seed_data

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"


def main() -> int:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js is required")
    # Refuse to reuse an unrelated service or run tests against its data.
    for port in (8001, 3001):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    original_url = make_url(get_settings().database_url)
    name = "splitbill_e2e_" + uuid4().hex
    admin = create_engine(
        original_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
        connect_args={"connect_timeout": 3},
    )
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = original_url.set(database=name)
    engine = create_engine(url, poolclass=NullPool, connect_args={"connect_timeout": 3})
    api_process = None
    previous_url = os.environ.get("DATABASE_URL")
    try:
        os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
        get_settings.cache_clear()
        command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
        with Session(engine) as session, session.begin():
            seed_data(session)
        environment = os.environ.copy()
        environment["CORS_ORIGINS"] = json.dumps(["http://127.0.0.1:3001"])
        environment["NEXT_PUBLIC_API_BASE_URL"] = "http://127.0.0.1:8001"
        environment["NEXT_TELEMETRY_DISABLED"] = "1"
        with tempfile.TemporaryFile(mode="w+b") as log:
            api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8001",
                ],
                cwd=BACKEND,
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            for _ in range(40):
                if api_process.poll() is not None:
                    raise RuntimeError("Test API exited before it was ready")
                try:
                    with urlopen("http://127.0.0.1:8001/ready", timeout=2) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError):
                    time.sleep(0.5)
            else:
                raise RuntimeError("Test API did not become ready")
            result = subprocess.run(
                [node, "node_modules/@playwright/test/cli.js", "test", *sys.argv[1:]],
                cwd=FRONTEND,
                env=environment,
                check=False,
            )
            return result.returncode
    finally:
        if api_process is not None:
            api_process.terminate()
            try:
                api_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                api_process.kill()
                api_process.wait()
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
        get_settings.cache_clear()
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
