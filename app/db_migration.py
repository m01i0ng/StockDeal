from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy import Column, DateTime, String, Table, func, select
from sqlalchemy.engine import Connection

from app.config import settings
from app.db import Base, engine

_logger = logging.getLogger(__name__)

_schema_migrations = Table(
    "schema_migrations",
    Base.metadata,
    Column("version", String(50), primary_key=True),
    Column("applied_at", DateTime, nullable=False, server_default=func.now()),
)

MigrationFn = Callable[[Connection], None]


def _migration_0001_initial(connection: Connection) -> None:
    """初始化业务表结构。"""
    from app.models.db import models as _  # noqa: F401

    Base.metadata.create_all(bind=connection)


_MIGRATIONS: list[tuple[str, MigrationFn]] = [
    ("0001_initial", _migration_0001_initial),
]


def _ensure_migrations_table(connection: Connection) -> None:
    """确保迁移表存在。"""
    _schema_migrations.create(bind=connection, checkfirst=True)


def _get_applied_versions(connection: Connection) -> set[str]:
    _ensure_migrations_table(connection)
    rows = connection.execute(select(_schema_migrations.c.version)).fetchall()
    return {row[0] for row in rows}


def run_migrations() -> None:
    """按版本顺序执行迁移。"""
    if not settings.db_auto_migrate:
        _logger.info("已跳过数据库迁移（DB_AUTO_MIGRATE=false）")
        return

    with engine.begin() as connection:
        applied = _get_applied_versions(connection)
        for version, fn in _MIGRATIONS:
            if version in applied:
                continue
            _logger.info("开始执行迁移: %s", version)
            fn(connection)
            connection.execute(_schema_migrations.insert().values(version=version))
            _logger.info("迁移完成: %s", version)
