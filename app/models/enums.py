from __future__ import annotations

from enum import Enum


class FundTradeType(str, Enum):
    """交易方向。"""

    buy = "buy"
    sell = "sell"


class FundTradeStatus(str, Enum):
    """交易状态。"""

    pending = "pending"
    confirmed = "confirmed"
    canceled = "canceled"
