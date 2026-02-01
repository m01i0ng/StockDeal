from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import (
    FundConversionCreateRequest,
    FundConversionResponse,
    FundHoldingPositionResponse,
    FundHoldingTransactionCreateRequest,
    FundHoldingTransactionResponse,
)
from app.services.fund import (
    fund_account_service,
    fund_conversion_service,
    fund_holding_service,
)

router = APIRouter(prefix="/fund-holdings", tags=["fund-holdings"])


@router.get(
    "",
    response_model=list[FundHoldingPositionResponse],
    summary="持仓列表",
    description="按账户获取持仓列表，可选基金代码过滤。",
    response_description="持仓列表",
)
def list_fund_holdings(
    account_id: int = Query(..., description="账户 ID", examples=[1]),
    fund_code: str | None = Query(None, description="基金代码", examples=["161725"]),
    db: Session = Depends(get_db),
) -> list[FundHoldingPositionResponse]:
    """获取账户持仓列表。"""
    return fund_account_service.list_account_holdings(db, account_id, fund_code)


@router.post(
    "/transactions",
    response_model=FundHoldingTransactionResponse,
    summary="新增交易",
    description="新增持仓交易记录并更新持仓。",
    response_description="交易记录",
)
def create_fund_transaction(
    payload: FundHoldingTransactionCreateRequest,
    db: Session = Depends(get_db),
) -> FundHoldingTransactionResponse:
    """新增持仓交易。"""
    return fund_holding_service.create_transaction(db, payload)


@router.get(
    "/transactions",
    response_model=list[FundHoldingTransactionResponse],
    summary="交易记录",
    description="按账户查询交易记录，可选基金代码过滤。",
    response_description="交易记录列表",
)
def list_fund_transactions(
    account_id: int = Query(..., description="账户 ID", examples=[1]),
    fund_code: str | None = Query(None, description="基金代码", examples=["161725"]),
    db: Session = Depends(get_db),
) -> list[FundHoldingTransactionResponse]:
    """获取账户交易记录。"""
    return fund_holding_service.list_transactions(db, account_id, fund_code)


@router.post(
    "/conversions",
    response_model=FundConversionResponse,
    summary="新增转换",
    description="新增基金转换记录并生成买卖交易。",
    response_description="转换记录",
)
def create_fund_conversion(
    payload: FundConversionCreateRequest,
    db: Session = Depends(get_db),
) -> FundConversionResponse:
    """新增基金转换。"""
    return fund_conversion_service.create_conversion(db, payload)


@router.get(
    "/conversions",
    response_model=list[FundConversionResponse],
    summary="转换记录",
    description="按账户查询基金转换记录。",
    response_description="转换记录列表",
)
def list_fund_conversions(
    account_id: int = Query(..., description="账户 ID", examples=[1]),
    db: Session = Depends(get_db),
) -> list[FundConversionResponse]:
    """获取账户转换记录。"""
    return fund_conversion_service.list_conversions(db, account_id)
