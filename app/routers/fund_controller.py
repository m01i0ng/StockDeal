from fastapi import APIRouter, Path, Query
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import (
    FundNavHistoryPeriod,
    FundNavHistoryResponse,
    FundRealtimeEstimateResponse,
    FundSnapshotResponse,
)
from app.services.fund import fund_service

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get(
    "/{code}/snapshot",
    response_model=FundSnapshotResponse,
    summary="基金快照",
    description="按基金代码返回基本信息、最新净值与持仓列表。",
    response_description="基金快照数据",
)
async def get_fund_snapshot(
    code: str = Path(..., description="基金代码", examples=["161725"]),
) -> FundSnapshotResponse:
    """按基金代码返回基本信息与最新持仓"""
    return await run_in_threadpool(fund_service.get_fund_snapshot, code)


@router.get(
    "/{code}/nav-history",
    response_model=FundNavHistoryResponse,
    summary="历史净值",
    description="按基金代码返回指定周期内的历史净值数据。",
    response_description="历史净值列表",
)
async def get_fund_nav_history(
    code: str = Path(..., description="基金代码", examples=["161725"]),
    period: FundNavHistoryPeriod = Query(
        FundNavHistoryPeriod.since_inception,
        description="查询周期",
        examples=[FundNavHistoryPeriod.since_inception.value],
    ),
) -> FundNavHistoryResponse:
    """按基金代码返回历史净值"""
    return await run_in_threadpool(fund_service.get_fund_nav_history, code, period)


@router.get(
    "/{code}/realtime-estimate",
    response_model=FundRealtimeEstimateResponse,
    summary="实时预估净值",
    description="按基金代码返回实时预估净值、涨幅与持仓贡献明细。",
    response_description="实时预估净值数据",
)
async def get_fund_realtime_estimate(
    code: str = Path(..., description="基金代码", examples=["161725"]),
) -> FundRealtimeEstimateResponse:
    """按基金代码返回实时预估净值与涨幅"""
    return await run_in_threadpool(fund_service.get_fund_realtime_estimate, code)
