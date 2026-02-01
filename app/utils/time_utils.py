from __future__ import annotations

from datetime import datetime, timedelta, timezone

CST_TZ = timezone(timedelta(hours=8))


def cst_now() -> datetime:
    """获取当前 CST 时间（返回无时区信息的时间对象）。"""
    return datetime.now(tz=CST_TZ).replace(tzinfo=None)


def to_cst(dt: datetime) -> datetime:
    """转换为 CST 时间（返回无时区信息的时间对象）。"""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(CST_TZ).replace(tzinfo=None)


def ensure_cst(dt: datetime | None) -> datetime:
    """将时间归一化为 CST 时间。"""
    if dt is None:
        return cst_now()
    return to_cst(dt)
