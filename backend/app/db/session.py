from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)


def init_db() -> None:
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Could not connect to MySQL. Create the careerpilot database and set "
            "MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE in .env. "
            "Example: CREATE DATABASE careerpilot CHARACTER SET utf8mb4;"
        ) from exc


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
