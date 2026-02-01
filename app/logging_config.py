"""日志配置与 trace_id 绑定。"""

from __future__ import annotations

import contextvars
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default="-"
)


class TraceIdFilter(logging.Filter):
    """为日志记录注入 trace_id。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = _trace_id_var.get() or "-"
        return True


def bind_trace_id(trace_id: str) -> contextvars.Token:
    """绑定 trace_id 到当前上下文。"""
    return _trace_id_var.set(trace_id or "-")


def reset_trace_id(token: contextvars.Token) -> None:
    """重置 trace_id 上下文。"""
    _trace_id_var.reset(token)


def get_trace_id() -> str:
    """获取当前上下文的 trace_id。"""
    return _trace_id_var.get()


def setup_logging(
    log_file: str,
    log_level: str,
    max_bytes: int,
    backup_count: int,
    enable_console: bool = True,
) -> None:
    """初始化日志配置，输出到文件（可选控制台）。"""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] [trace_id=%(trace_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(TraceIdFilter())

    handlers: list[logging.Handler] = [file_handler]

    if enable_console:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(TraceIdFilter())
        handlers.append(stream_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(log_level)


def configure_logger_level(logger_name: str, level: Optional[str]) -> None:
    """按需调整指定 logger 的级别。"""
    if not level:
        return
    logging.getLogger(logger_name).setLevel(level)
