from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.schemas import (
    FundAccountCreateRequest,
    FundAccountDetailResponse,
    FundAccountResponse,
    FundAccountSummaryResponse,
    FundAccountUpdateRequest,
)
from app.services.fund import fund_account_service

router = APIRouter(prefix="/fund-accounts", tags=["fund-accounts"])


@router.post(
    "",
    response_model=FundAccountResponse,
    summary="创建基金账户",
    description="创建新的基金账户。",
    response_description="基金账户信息",
)
def create_fund_account(
    payload: FundAccountCreateRequest,
    db: Session = Depends(get_db),
) -> FundAccountResponse:
    """创建基金账户。"""
    return fund_account_service.create_account(db, payload)


@router.get(
    "",
    response_model=list[FundAccountResponse],
    summary="账户列表",
    description="返回全部基金账户。",
    response_description="基金账户列表",
)
def list_fund_accounts(db: Session = Depends(get_db)) -> list[FundAccountResponse]:
    """获取基金账户列表。"""
    return fund_account_service.list_accounts(db)


@router.put(
    "/{account_id}",
    response_model=FundAccountResponse,
    summary="更新账户",
    description="更新账户名称、备注与默认买入费率。",
    response_description="更新后的账户信息",
)
def update_fund_account(
    account_id: int,
    payload: FundAccountUpdateRequest,
    db: Session = Depends(get_db),
) -> FundAccountResponse:
    """更新基金账户。"""
    return fund_account_service.update_account(db, account_id, payload)


@router.get(
    "/{account_id}",
    response_model=FundAccountDetailResponse,
    summary="账户详情",
    description="返回账户详情与持仓列表。",
    response_description="账户详情",
)
def get_fund_account_detail(
    account_id: int,
    db: Session = Depends(get_db),
) -> FundAccountDetailResponse:
    """获取账户详情与持仓列表。"""
    return fund_account_service.get_account_detail(db, account_id)


@router.get(
    "/{account_id}/summary",
    response_model=FundAccountSummaryResponse,
    summary="账户汇总",
    description="返回账户汇总指标（总成本/总市值/总盈亏）。",
    response_description="账户汇总指标",
)
def get_fund_account_summary(
    account_id: int,
    db: Session = Depends(get_db),
) -> FundAccountSummaryResponse:
    """获取账户汇总指标。"""
    return fund_account_service.get_account_summary(db, account_id)
