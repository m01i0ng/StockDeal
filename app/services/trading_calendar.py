from __future__ import annotations

from datetime import date as dt_date
from typing import Iterable

import akshare as ak
import pandas as pd

_trade_dates: set[dt_date] | None = None


def is_trading_day(date_value: dt_date) -> bool:
    """判断是否为交易日（含节假日）。"""
    trade_dates = _get_trade_dates()
    if not trade_dates:
        return date_value.weekday() < 5
    return date_value in trade_dates


def _get_trade_dates() -> set[dt_date]:
    global _trade_dates
    if _trade_dates is None:
        _trade_dates = _load_trade_dates()
    return _trade_dates


def _load_trade_dates() -> set[dt_date]:
    trade_df = ak.tool_trade_date_hist_sina()
    if trade_df.empty:
        return set()
    date_series = _extract_trade_date_series(trade_df)
    return {value.date() for value in pd.to_datetime(date_series)}


def _extract_trade_date_series(trade_df: pd.DataFrame) -> Iterable[str]:
    for col in ("trade_date", "date", "交易日期", "交易日"):
        if col in trade_df.columns:
            return trade_df[col]
    return trade_df.iloc[:, 0]
