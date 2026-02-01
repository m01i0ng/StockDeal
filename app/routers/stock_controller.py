from fastapi import APIRouter, Path
from fastapi.concurrency import run_in_threadpool

from app.models.schemas import StockRealtimeQuoteResponse
from app.services.stock import stock_service

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get(
    "/{code}/realtime",
    response_model=StockRealtimeQuoteResponse,
    summary="实时行情",
    description="按股票代码返回实时行情数据。",
    response_description="实时行情数据",
)
async def get_stock_realtime_quote(
    code: str = Path(..., description="股票代码", examples=["600519"]),
) -> StockRealtimeQuoteResponse:
    """按股票代码返回实时行情"""
    return await run_in_threadpool(stock_service.get_stock_realtime_quote, code)
