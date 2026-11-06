from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from config import settings

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def _connect_args() -> dict:
    schema = settings.DB_SCHEMA
    if schema:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
            raise RuntimeError("Nama DB_SCHEMA tidak valid.")
        return {"options": f"-csearch_path={schema},public"}
    return {}


def configure_engine(url: Optional[str] = None) -> Engine:
    global _engine, _session_factory
    url = url or settings.database_url()
    if not url:
        raise RuntimeError("DATABASE_URL belum dikonfigurasi. Salin .env.example menjadi .env.")
    _engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
        connect_args=_connect_args(),
    )
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return _engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        configure_engine()
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        configure_engine()
    assert _session_factory is not None
    return _session_factory


def get_session() -> Session:
    return get_session_factory()()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def check_connection() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def create_schema_if_needed() -> None:
    schema = settings.DB_SCHEMA
    if not schema:
        return
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise RuntimeError("Nama DB_SCHEMA tidak valid.")
    with get_engine().begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))


def database_ready() -> bool:
    try:
        engine = get_engine()
        inspector = inspect(engine)
        schema = settings.DB_SCHEMA or None
        return inspector.has_table("prestasi", schema=schema)
    except Exception:
        return False


def masked_database_info() -> str:
    url = settings.database_url()
    if not url:
        return "Belum dikonfigurasi"
    try:
        parsed = make_url(url)
        host = parsed.host or "localhost"
        port = parsed.port or 5432
        return f"{parsed.username}@{host}:{port}/{parsed.database}"
    except Exception:
        return "Konfigurasi database tidak valid"
