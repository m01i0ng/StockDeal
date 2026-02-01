from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import FundAccountNotFoundError
from app.models.db.models import FundAccount, FundHolding
from app.models.schemas import (
    FundAccountCreateRequest,
    FundAccountDetailResponse,
    FundAccountResponse,
    FundAccountSummaryResponse,
    FundAccountUpdateRequest,
    FundHoldingPositionResponse,
)
from app.services.fund import fund_service
from app.utils.parsing import parse_float


def create_account(
    db: Session, payload: FundAccountCreateRequest
) -> FundAccountResponse:
    """创建基金账户。"""
    account = FundAccount(
        name=payload.name,
        remark=payload.remark,
        default_buy_fee_percent=payload.default_buy_fee_percent,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return FundAccountResponse(
        id=account.id,
        name=account.name,
        remark=account.remark,
        default_buy_fee_percent=account.default_buy_fee_percent,
        created_at=account.created_at,
    )


def list_accounts(db: Session) -> list[FundAccountResponse]:
    """获取账户列表。"""
    accounts = db.execute(select(FundAccount).order_by(FundAccount.id)).scalars().all()
    return [
        FundAccountResponse(
            id=account.id,
            name=account.name,
            remark=account.remark,
            default_buy_fee_percent=account.default_buy_fee_percent,
            created_at=account.created_at,
        )
        for account in accounts
    ]


def update_account(
    db: Session,
    account_id: int,
    payload: FundAccountUpdateRequest,
) -> FundAccountResponse:
    """更新基金账户。"""
    account = db.get(FundAccount, account_id)
    if account is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")
    if payload.name is not None:
        account.name = payload.name
    if payload.remark is not None:
        account.remark = payload.remark
    if payload.default_buy_fee_percent is not None:
        account.default_buy_fee_percent = payload.default_buy_fee_percent
    db.commit()
    db.refresh(account)
    return FundAccountResponse(
        id=account.id,
        name=account.name,
        remark=account.remark,
        default_buy_fee_percent=account.default_buy_fee_percent,
        created_at=account.created_at,
    )


def get_account_detail(db: Session, account_id: int) -> FundAccountDetailResponse:
    """获取账户详情与持仓。"""
    account = db.get(FundAccount, account_id)
    if account is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")
    holdings = (
        db.execute(select(FundHolding).where(FundHolding.account_id == account_id))
        .scalars()
        .all()
    )
    holding_responses = [_build_holding_position(holding) for holding in holdings]
    summary = _build_account_summary(holding_responses)
    return FundAccountDetailResponse(
        id=account.id,
        name=account.name,
        remark=account.remark,
        created_at=account.created_at,
        holdings=holding_responses,
        default_buy_fee_percent=account.default_buy_fee_percent,
        total_cost=summary.total_cost,
        total_value=summary.total_value,
        total_profit=summary.total_profit,
        total_profit_percent=summary.total_profit_percent,
    )


def get_account_summary(db: Session, account_id: int) -> FundAccountSummaryResponse:
    """获取账户汇总指标。"""
    if db.get(FundAccount, account_id) is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")
    holdings = (
        db.execute(select(FundHolding).where(FundHolding.account_id == account_id))
        .scalars()
        .all()
    )
    holding_responses = [_build_holding_position(holding) for holding in holdings]
    summary = _build_account_summary(holding_responses, account_id)
    return FundAccountSummaryResponse(
        account_id=summary.account_id,
        total_cost=summary.total_cost,
        total_value=summary.total_value,
        total_profit=summary.total_profit,
        total_profit_percent=summary.total_profit_percent,
    )


def list_account_holdings(
    db: Session, account_id: int, fund_code: str | None = None
) -> list[FundHoldingPositionResponse]:
    """获取账户持仓列表。"""
    if db.get(FundAccount, account_id) is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")
    stmt = select(FundHolding).where(FundHolding.account_id == account_id)
    if fund_code:
        stmt = stmt.where(FundHolding.fund_code == str(fund_code).strip())
    holdings = db.execute(stmt).scalars().all()
    return [_build_holding_position(holding) for holding in holdings]


def _build_holding_position(holding: FundHolding) -> FundHoldingPositionResponse:
    estimate = fund_service.get_fund_realtime_estimate(holding.fund_code)
    estimated_nav = parse_float(estimate.estimated_nav)
    if estimated_nav is None:
        estimated_nav = parse_float(estimate.nav.nav)
    estimated_value = None
    estimated_profit = None
    estimated_profit_percent = None
    if estimated_nav is not None:
        estimated_value = holding.total_shares * estimated_nav
        estimated_profit = estimated_value - holding.total_amount
        if holding.total_amount > 0:
            estimated_profit_percent = estimated_profit / holding.total_amount * 100
    return FundHoldingPositionResponse(
        holding_id=holding.id,
        account_id=holding.account_id,
        fund_code=holding.fund_code,
        total_amount=holding.total_amount,
        total_shares=holding.total_shares,
        estimated_nav=estimated_nav,
        estimated_value=estimated_value,
        estimated_profit=estimated_profit,
        estimated_profit_percent=estimated_profit_percent,
        updated_at=holding.updated_at,
    )


def _build_account_summary(
    holding_responses: list[FundHoldingPositionResponse],
    account_id: int | None = None,
) -> FundAccountSummaryResponse:
    total_cost = sum(item.total_amount for item in holding_responses)
    total_value = None
    total_profit = None
    total_profit_percent = None
    if holding_responses and all(
        item.estimated_value is not None for item in holding_responses
    ):
        total_value = sum(
            item.estimated_value
            for item in holding_responses
            if item.estimated_value is not None
        )
        total_profit = total_value - total_cost
        if total_cost > 0:
            total_profit_percent = total_profit / total_cost * 100
    return FundAccountSummaryResponse(
        account_id=account_id or 0,
        total_cost=total_cost,
        total_value=total_value,
        total_profit=total_profit,
        total_profit_percent=total_profit_percent,
    )
