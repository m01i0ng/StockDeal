from __future__ import annotations

import datetime
from typing import Any, Callable, TypeVar

import akshare as ak
import pandas as pd

from app.exceptions import FundNotFoundError
from app.models.schemas import (
    BasicInfoItem,
    FundHolding,
    FundHoldingEstimate,
    FundNav,
    FundNavHistoryItem,
    FundNavHistoryPeriod,
    FundNavHistoryResponse,
    FundRealtimeEstimateResponse,
    FundSnapshotResponse,
)
from app.services.cache import (
    get_fund_basic_info_cache,
    get_fund_latest_holdings_cache,
    get_fund_list_cache,
    get_fund_realtime_estimate_cache,
)
from app.services.stock import stock_service
from app.utils.parsing import parse_float, parse_percent

T = TypeVar("T")


def _resolve_fund_by_code(code: str) -> dict:
    """根据基金代码解析基金"""
    fund_list = get_fund_list_cache()
    code = str(code).strip()
    match = fund_list[fund_list["基金代码"] == code]

    if match.empty:
        raise FundNotFoundError(f"未找到匹配基金代码: {code}")

    row = match.iloc[0]
    return {
        "code": row["基金代码"],
        "name": row["基金简称"],
        "type": row["基金类型"],
    }


def _get_basic_info(code: str) -> list[BasicInfoItem]:
    """获取基金基本信息"""
    info_df = ak.fund_individual_basic_info_xq(symbol=code)
    return [
        BasicInfoItem(item=str(row["item"]), value=str(row["value"]))
        for _, row in info_df.iterrows()
    ]


def _get_basic_info_cached(code: str) -> list[BasicInfoItem]:
    def _loader() -> list[dict[str, str | None]]:
        info_df = ak.fund_individual_basic_info_xq(symbol=code)
        return [
            {
                "item": str(row["item"]),
                "value": str(row["value"]) if row["value"] is not None else None,
            }
            for _, row in info_df.iterrows()
        ]

    return _load_cached_list(
        code,
        _loader,
        get_fund_basic_info_cache,
        lambda row: BasicInfoItem(item=str(row.get("item")), value=row.get("value")),
    )


def _latest_nav_open_fund(code: str) -> FundNav:
    """开放式基金最新净值"""
    nav_df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
    latest = nav_df.iloc[-1]
    return FundNav(date=latest["净值日期"], nav=float(latest["单位净值"]))


def _latest_nav_money_fund(code: str) -> FundNav:
    """货币型基金最新净值"""
    nav_df = ak.fund_money_fund_info_em(symbol=code)
    latest = nav_df.iloc[-1]
    nav = float(latest["每万份收益"])
    nav_7d = float(latest["7日年化收益率"])
    return FundNav(date=latest["净值日期"], nav=nav, nav_7d=nav_7d)


def _extract_quarter(value: str, year: int) -> int | None:
    """从季度描述中提取季度数"""
    if not isinstance(value, str):
        return None
    if f"{year}年" not in value:
        return None
    for q in range(4, 0, -1):
        if f"{q}季度" in value:
            return q
    return None


def _latest_quarter_holdings_by_year(code: str, year: int) -> pd.DataFrame | None:
    """获取指定年份最后一个季度的持仓数据"""
    holdings = ak.fund_portfolio_hold_em(symbol=code, date=year)
    if holdings.empty:
        return None

    quarters = holdings["季度"].apply(lambda x: _extract_quarter(x, year))
    if quarters.isna().all():
        return None

    latest_quarter = int(quarters.dropna().max())
    return holdings[
        holdings["季度"].str.contains(f"{year}年{latest_quarter}季度", na=False)
    ]


def _latest_quarter_holdings(code: str) -> pd.DataFrame | None:
    """当前年份无数据时回退上一年"""
    year = datetime.datetime.now().year
    for y in [year, year - 1]:
        result = _latest_quarter_holdings_by_year(code, y)
        if result is not None and not result.empty:
            return result
    return None


def _format_holdings(holdings: pd.DataFrame | None) -> list[FundHolding]:
    """以可读方式输出持仓与占比"""
    if holdings is None or holdings.empty:
        return []

    output: list[FundHolding] = []
    for _, row in holdings.iterrows():
        weight = pd.to_numeric(row.get("占净值比例"), errors="coerce")
        market_value = pd.to_numeric(row.get("持仓市值"), errors="coerce")
        output.append(
            FundHolding(
                quarter=str(row.get("季度")),
                stock_code=str(row.get("股票代码")),
                stock_name=str(row.get("股票名称")),
                weight_percent=(f"{weight:.2f}%" if pd.notna(weight) else None),
                market_value=(
                    f"{market_value:,.2f}" if pd.notna(market_value) else None
                ),
            )
        )
    return output


def _get_latest_holdings_cached(code: str) -> list[FundHolding]:
    def _loader() -> list[dict[str, str | None]]:
        holdings_df = _latest_quarter_holdings(code)
        holdings = _format_holdings(holdings_df)
        return [holding.model_dump() for holding in holdings]

    return _load_cached_list(
        code,
        _loader,
        get_fund_latest_holdings_cache,
        lambda row: FundHolding(**row),
    )


def _load_cached_list(
    code: str,
    loader: Callable[[], list[dict[str, Any]]],
    cache_getter: Callable[
        [str, Callable[[], list[dict[str, Any]]]],
        list[dict[str, Any]],
    ],
    mapper: Callable[[dict[str, Any]], T],
) -> list[T]:
    cached = cache_getter(code, loader)
    return [mapper(row) for row in cached]


def _get_stock_change_percents(codes: list[str]) -> dict[str, float | None]:
    """批量获取股票实时涨幅"""
    if not codes:
        return {}
    try:
        quotes = stock_service.get_stock_realtime_quotes(codes)
    except (ValueError, RuntimeError):
        return {code: None for code in codes}
    return {code: quotes[code].change_percent for code in codes if code in quotes}


def _estimate_from_holdings(
    holdings: pd.DataFrame | None,
) -> tuple[list[FundHoldingEstimate], list[str], float | None]:
    if holdings is None or holdings.empty:
        return [], [], None

    stock_codes = [str(row.get("股票代码")) for _, row in holdings.iterrows()]
    change_percent_map = _get_stock_change_percents(stock_codes)
    details: list[FundHoldingEstimate] = []
    skipped: list[str] = []
    total_contribution = 0.0
    has_valid = False

    for _, row in holdings.iterrows():
        stock_code = str(row.get("股票代码"))
        stock_name = str(row.get("股票名称"))
        weight = parse_percent(row.get("占净值比例"))
        change_percent = change_percent_map.get(stock_code)
        contribution = None

        if weight is None or change_percent is None:
            skipped.append(stock_code)
        else:
            contribution = weight * change_percent / 100
            total_contribution += contribution
            has_valid = True

        details.append(
            FundHoldingEstimate(
                stock_code=stock_code,
                stock_name=stock_name,
                weight_percent=(f"{weight:.2f}%" if weight is not None else None),
                change_percent=change_percent,
                contribution_percent=contribution,
            )
        )

    estimated_growth = total_contribution if has_valid else None
    return details, skipped, estimated_growth


def _filter_history_by_period(
    nav_df: pd.DataFrame,
    date_col: str,
    period: FundNavHistoryPeriod,
) -> pd.DataFrame:
    """按时间维度过滤历史净值"""
    if period == FundNavHistoryPeriod.since_inception:
        return nav_df

    period_days = {
        FundNavHistoryPeriod.one_week: 7,
        FundNavHistoryPeriod.one_month: 30,
        FundNavHistoryPeriod.three_months: 90,
        FundNavHistoryPeriod.one_year: 365,
    }

    nav_df = nav_df.copy()
    nav_df[date_col] = pd.to_datetime(nav_df[date_col])
    end_date = nav_df[date_col].max()
    start_date = end_date - pd.Timedelta(days=period_days[period])
    return nav_df[nav_df[date_col] >= start_date]


def get_fund_nav_history(
    code: str,
    period: FundNavHistoryPeriod,
) -> FundNavHistoryResponse:
    """获取基金历史净值数据"""
    meta = _resolve_fund_by_code(code)

    if "货币型" in meta["type"]:
        nav_df = ak.fund_money_fund_info_em(symbol=meta["code"])
        nav_df = _filter_history_by_period(nav_df, "净值日期", period)
        data = [
            FundNavHistoryItem(
                date=row["净值日期"],
                nav=float(row["每万份收益"]),
                nav_7d=float(row["7日年化收益率"]),
            )
            for _, row in nav_df.iterrows()
        ]
    else:
        nav_df = ak.fund_open_fund_info_em(
            symbol=meta["code"], indicator="单位净值走势"
        )
        nav_df = _filter_history_by_period(nav_df, "净值日期", period)
        data = [
            FundNavHistoryItem(
                date=row["净值日期"],
                nav=float(row["单位净值"]),
                daily_growth=float(row["日增长率"]),
            )
            for _, row in nav_df.iterrows()
        ]

    return FundNavHistoryResponse(
        code=meta["code"],
        name=meta["name"],
        type=meta["type"],
        period=period,
        data=data,
    )


def get_fund_snapshot(code: str) -> FundSnapshotResponse:
    """根据基金代码获取基本信息、最新净值与最新季度持仓"""
    meta = _resolve_fund_by_code(code)
    basic_info = _get_basic_info_cached(meta["code"])

    if "货币型" in meta["type"]:
        nav = _latest_nav_money_fund(meta["code"])
    else:
        nav = _latest_nav_open_fund(meta["code"])

    holdings = _get_latest_holdings_cached(meta["code"])

    return FundSnapshotResponse(
        code=meta["code"],
        name=meta["name"],
        type=meta["type"],
        basic_info=basic_info,
        nav=nav,
        holdings=holdings,
    )


def get_fund_realtime_estimate(code: str) -> FundRealtimeEstimateResponse:
    """根据基金持仓与股票实时涨幅计算预估净值与涨幅"""
    meta = _resolve_fund_by_code(code)

    def _loader() -> dict[str, Any]:
        if "货币型" in meta["type"]:
            nav = _latest_nav_money_fund(meta["code"])
        else:
            nav = _latest_nav_open_fund(meta["code"])

        holdings_df = _latest_quarter_holdings(meta["code"])
        holdings, skipped, estimated_growth = _estimate_from_holdings(holdings_df)

        nav_value = parse_float(nav.nav)
        estimated_nav = None
        if nav_value is not None and estimated_growth is not None:
            estimated_nav = nav_value * (1 + estimated_growth / 100)

        response = FundRealtimeEstimateResponse(
            code=meta["code"],
            name=meta["name"],
            type=meta["type"],
            nav=nav,
            estimated_nav=estimated_nav,
            estimated_growth_percent=estimated_growth,
            holdings=holdings,
            skipped=skipped,
        )
        return response.model_dump(mode="json")

    cached = get_fund_realtime_estimate_cache(meta["code"], _loader)
    return FundRealtimeEstimateResponse(**cached)
