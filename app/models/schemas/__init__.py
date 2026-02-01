from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.enums import FundTradeStatus, FundTradeType


class BasicInfoItem(BaseModel):
    item: str = Field(..., description="字段名称", examples=["基金经理"])
    value: str | None = Field(
        default=None,
        description="字段值",
        examples=["张三"],
    )


class FundNav(BaseModel):
    date: dt_date | str = Field(..., description="净值日期", examples=["2025-01-31"])
    nav: float | str = Field(..., description="单位净值", examples=[1.2345])
    nav_7d: float | str | None = Field(
        default=None,
        description="七日年化（货币型基金）",
        examples=[1.56],
    )


class FundHolding(BaseModel):
    quarter: str = Field(..., description="季度", examples=["2024Q4"])
    stock_code: str = Field(..., description="股票代码", examples=["600519"])
    stock_name: str = Field(..., description="股票名称", examples=["贵州茅台"])
    weight_percent: str | None = Field(
        default=None,
        description="占净值比例",
        examples=["5.23%"],
    )
    market_value: str | None = Field(
        default=None,
        description="持仓市值",
        examples=["1,234.56"],
    )


class FundNavHistoryPeriod(str, Enum):
    one_week = "one_week"
    one_month = "one_month"
    three_months = "three_months"
    one_year = "one_year"
    since_inception = "since_inception"


class FundNavHistoryItem(BaseModel):
    date: dt_date | str = Field(..., description="净值日期", examples=["2025-01-31"])
    nav: float | str = Field(..., description="单位净值", examples=[1.2345])
    daily_growth: float | str | None = Field(
        default=None,
        description="日涨幅（百分比）",
        examples=[0.58],
    )
    nav_7d: float | str | None = Field(
        default=None,
        description="七日年化（货币型基金）",
        examples=[1.56],
    )


class FundNavHistoryResponse(BaseModel):
    code: str = Field(..., description="基金代码", examples=["161725"])
    name: str | None = Field(
        default=None, description="基金名称", examples=["招商中证白酒"]
    )
    type: str | None = Field(default=None, description="基金类型", examples=["指数型"])
    period: str = Field(..., description="查询周期", examples=["one_year"])
    data: list[FundNavHistoryItem] = Field(..., description="历史净值列表")


class FundSnapshotResponse(BaseModel):
    code: str = Field(..., description="基金代码", examples=["161725"])
    name: str | None = Field(
        default=None, description="基金名称", examples=["招商中证白酒"]
    )
    type: str | None = Field(default=None, description="基金类型", examples=["指数型"])
    basic_info: list[BasicInfoItem] = Field(..., description="基金基本信息")
    nav: FundNav = Field(..., description="最新净值信息")
    holdings: list[FundHolding] = Field(..., description="最新持仓")


class FundHoldingEstimate(BaseModel):
    stock_code: str = Field(..., description="股票代码", examples=["600519"])
    stock_name: str = Field(..., description="股票名称", examples=["贵州茅台"])
    weight_percent: str | None = Field(
        default=None,
        description="持仓占比",
        examples=["5.23%"],
    )
    change_percent: float | None = Field(
        default=None,
        description="股票涨跌幅（百分比）",
        examples=[1.23],
    )
    contribution_percent: float | None = Field(
        default=None,
        description="对基金预估涨幅的贡献（百分比）",
        examples=[0.12],
    )


class FundRealtimeEstimateResponse(BaseModel):
    code: str = Field(..., description="基金代码", examples=["161725"])
    name: str | None = Field(
        default=None, description="基金名称", examples=["招商中证白酒"]
    )
    type: str | None = Field(default=None, description="基金类型", examples=["指数型"])
    nav: FundNav = Field(..., description="最新净值信息")
    estimated_nav: float | None = Field(
        default=None,
        description="预估净值",
        examples=[1.4567],
    )
    estimated_growth_percent: float | None = Field(
        default=None,
        description="预估涨幅（百分比）",
        examples=[0.56],
    )
    holdings: list[FundHoldingEstimate] = Field(..., description="预估持仓贡献明细")
    skipped: list[str] = Field(..., description="缺失行情的股票代码列表")


class StockMarket(str, Enum):
    a_share = "A"
    h_share = "H"


class StockRealtimeQuoteResponse(BaseModel):
    code: str = Field(..., description="股票代码", examples=["600519"])
    market: StockMarket = Field(..., description="市场类型")
    latest_price: float | None = Field(
        default=None,
        description="最新价",
        examples=[123.45],
    )
    change_percent: float | None = Field(
        default=None,
        description="涨跌幅（百分比）",
        examples=[-0.32],
    )


class FundAccountCreateRequest(BaseModel):
    name: str = Field(..., description="账户名称", examples=["主账户"])
    remark: str | None = Field(default=None, description="备注", examples=["长期持有"])
    default_buy_fee_percent: float = Field(
        default=0.0, description="默认买入费率（百分比）", examples=[0.15]
    )


class FundAccountUpdateRequest(BaseModel):
    name: str | None = Field(default=None, description="账户名称", examples=["主账户"])
    remark: str | None = Field(default=None, description="备注", examples=["长期持有"])
    default_buy_fee_percent: float | None = Field(
        default=None, description="默认买入费率（百分比）", examples=[0.15]
    )


class FundAccountResponse(BaseModel):
    id: int = Field(..., description="账户 ID", examples=[1])
    name: str = Field(..., description="账户名称", examples=["主账户"])
    remark: str | None = Field(default=None, description="备注", examples=["长期持有"])
    default_buy_fee_percent: float = Field(
        ..., description="默认买入费率（百分比）", examples=[0.15]
    )
    created_at: datetime = Field(..., description="创建时间")


class FundHoldingPositionResponse(BaseModel):
    holding_id: int = Field(..., description="持仓 ID", examples=[1])
    account_id: int = Field(..., description="账户 ID", examples=[1])
    fund_code: str = Field(..., description="基金代码", examples=["161725"])
    total_amount: float = Field(..., description="持仓金额", examples=[10000.0])
    total_shares: float = Field(..., description="持仓份额", examples=[12345.67])
    estimated_nav: float | None = Field(default=None, description="预估净值")
    estimated_value: float | None = Field(default=None, description="预估估值")
    estimated_profit: float | None = Field(default=None, description="预估盈亏")
    estimated_profit_percent: float | None = Field(
        default=None, description="预估盈亏比例"
    )
    updated_at: datetime = Field(..., description="更新时间")


class FundAccountDetailResponse(FundAccountResponse):
    holdings: list[FundHoldingPositionResponse] = Field(
        default_factory=list, description="账户持仓列表"
    )
    total_cost: float = Field(..., description="总成本", examples=[10000.0])
    total_value: float | None = Field(
        default=None, description="总市值", examples=[12000.0]
    )
    total_profit: float | None = Field(
        default=None, description="总盈亏", examples=[2000.0]
    )
    total_profit_percent: float | None = Field(default=None, description="总盈亏比例")


class FundAccountSummaryResponse(BaseModel):
    account_id: int = Field(..., description="账户 ID", examples=[1])
    total_cost: float = Field(..., description="总成本", examples=[10000.0])
    total_value: float | None = Field(
        default=None, description="总市值", examples=[12000.0]
    )
    total_profit: float | None = Field(
        default=None, description="总盈亏", examples=[2000.0]
    )
    total_profit_percent: float | None = Field(default=None, description="总盈亏比例")


class FundHoldingTransactionCreateRequest(BaseModel):
    account_id: int = Field(..., description="账户 ID", examples=[1])
    fund_code: str = Field(..., description="基金代码", examples=["161725"])
    trade_type: FundTradeType = Field(..., description="交易方向")
    amount: float = Field(..., description="交易金额", examples=[1000.0])
    fee_percent: float | None = Field(
        default=None, description="手续费比例", examples=[0.15]
    )
    trade_date: dt_date = Field(..., description="交易日期", examples=["2025-01-31"])
    is_after_cutoff: bool = Field(default=False, description="是否为15点后交易")
    remark: str | None = Field(default=None, description="备注")


class FundHoldingCreateRequest(BaseModel):
    account_id: int = Field(..., description="账户 ID", examples=[1])
    fund_code: str = Field(..., description="基金代码", examples=["161725"])
    total_amount: float = Field(..., description="总额", examples=[12000.0])
    profit_amount: float = Field(..., description="收益额", examples=[2000.0])
    remark: str | None = Field(default=None, description="备注")


class FundHoldingUpdateRequest(BaseModel):
    total_amount: float = Field(..., description="持仓金额", examples=[10000.0])
    total_shares: float = Field(..., description="持仓份额", examples=[12345.67])


class FundHoldingTransactionResponse(BaseModel):
    id: int = Field(..., description="交易 ID", examples=[1])
    account_id: int = Field(..., description="账户 ID", examples=[1])
    holding_id: int | None = Field(default=None, description="持仓 ID")
    conversion_id: int | None = Field(default=None, description="转换记录 ID")
    fund_code: str = Field(..., description="基金代码", examples=["161725"])
    trade_type: FundTradeType = Field(..., description="交易方向")
    status: FundTradeStatus = Field(..., description="交易状态")
    amount: float = Field(..., description="交易金额")
    fee_percent: float = Field(..., description="手续费比例")
    fee_amount: float = Field(..., description="手续费金额")
    confirmed_nav: float = Field(..., description="确认净值")
    confirmed_nav_date: dt_date = Field(..., description="确认净值日期")
    shares: float = Field(..., description="确认份额")
    holding_amount: float | None = Field(default=None, description="持有金额")
    profit_amount: float | None = Field(default=None, description="盈利金额")
    trade_time: datetime = Field(..., description="交易时间")
    remark: str | None = Field(default=None, description="备注")


class FundConversionCreateRequest(BaseModel):
    account_id: int = Field(..., description="账户 ID", examples=[1])
    from_fund_code: str = Field(..., description="转出基金代码", examples=["161725"])
    to_fund_code: str = Field(..., description="转入基金代码", examples=["007119"])
    from_amount: float = Field(..., description="转出金额", examples=[1000.0])
    from_fee_percent: float | None = Field(
        default=None, description="转出手续费比例", examples=[0.15]
    )
    to_amount: float = Field(..., description="转入金额", examples=[980.0])
    to_fee_percent: float | None = Field(
        default=None, description="转入手续费比例", examples=[0.15]
    )
    trade_date: dt_date = Field(..., description="交易日期", examples=["2025-01-31"])
    is_after_cutoff: bool = Field(default=False, description="是否为15点后交易")
    remark: str | None = Field(default=None, description="备注")


class FundConversionResponse(BaseModel):
    id: int = Field(..., description="转换 ID", examples=[1])
    account_id: int = Field(..., description="账户 ID", examples=[1])
    from_fund_code: str = Field(..., description="转出基金代码", examples=["161725"])
    to_fund_code: str = Field(..., description="转入基金代码", examples=["007119"])
    trade_time: datetime = Field(..., description="交易时间")
    remark: str | None = Field(default=None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    from_transaction: FundHoldingTransactionResponse = Field(
        ..., description="转出交易记录"
    )
    to_transaction: FundHoldingTransactionResponse = Field(
        ..., description="转入交易记录"
    )
