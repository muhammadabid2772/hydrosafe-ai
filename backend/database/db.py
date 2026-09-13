from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        if configured.startswith("postgres://"):
            configured = "postgresql+psycopg://" + configured[len("postgres://"):]
        elif configured.startswith("postgresql://") and "+" not in configured.split("://", 1)[0]:
            configured = "postgresql+psycopg://" + configured[len("postgresql://"):]
        return configured
    path = Path(os.getenv("HYDROSAFE_DB_PATH", Path(__file__).resolve().parent / "hydrosafe.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


DATABASE_URL = _database_url()
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from .models import ReportRecord, UserRecord  # noqa: F401
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
