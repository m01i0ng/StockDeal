from __future__ import annotations

from typing import Any

import pandas as pd


def parse_float(value: Any) -> float | None:
    """解析浮点数，无法解析时返回 None。"""
    if value in (None, ""):
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_percent(value: Any) -> float | None:
    """解析百分比数值，支持带 % 的字符串。"""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.replace("%", "").replace(",", "").strip()
        try:
            return float(normalized)
        except ValueError:
            return None
    return None
