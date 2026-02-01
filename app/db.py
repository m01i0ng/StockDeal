from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy 基类。"""


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """初始化数据库（执行迁移）。"""
    from app.db_migration import run_migrations

    run_migrations()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
