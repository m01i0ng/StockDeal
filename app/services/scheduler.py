from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.db import SessionLocal
from app.services.fund import fund_holding_service
from app.time_utils import CST_TZ

_logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    """启动定时任务。"""
    global _scheduler
    if not settings.scheduler_enabled:
        _logger.info("定时任务已禁用")
        return
    if _scheduler is not None:
        return
    scheduler = BackgroundScheduler(timezone=CST_TZ)
    scheduler.add_job(
        _confirm_pending_trades,
        "cron",
        hour=settings.scheduler_confirm_hour,
        minute=settings.scheduler_confirm_minute,
        id="confirm_pending_trades",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    _logger.info("定时任务已启动")


def stop_scheduler() -> None:
    """停止定时任务。"""
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    _logger.info("定时任务已停止")


def _confirm_pending_trades() -> None:
    """确认待确认交易。"""
    db = SessionLocal()
    try:
        count = fund_holding_service.confirm_pending_transactions(db)
        if count:
            _logger.info("确认待确认交易数量: %s", count)
    except Exception as exc:
        _logger.exception("确认待确认交易失败: %s", exc)
    finally:
        db.close()
