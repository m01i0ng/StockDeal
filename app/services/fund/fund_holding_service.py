from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import FundAccountNotFoundError, FundHoldingNotFoundError
from app.models.db.models import FundAccount, FundHolding, FundTransaction
from app.models.enums import FundTradeStatus, FundTradeType
from app.models.schemas import (
    FundHoldingTransactionCreateRequest,
    FundHoldingTransactionResponse,
)
from app.services.trading_calendar import is_trading_day
from app.time_utils import cst_now, ensure_cst


def create_transaction(
    db: Session,
    payload: FundHoldingTransactionCreateRequest,
) -> FundHoldingTransactionResponse:
    """创建持仓交易记录。"""
    transaction = _create_transaction_record(
        db=db,
        account_id=payload.account_id,
        fund_code=payload.fund_code,
        trade_type=payload.trade_type,
        amount=payload.amount,
        fee_percent=payload.fee_percent,
        confirmed_nav=payload.confirmed_nav,
        trade_time=payload.trade_time,
        holding_amount=payload.holding_amount,
        profit_amount=payload.profit_amount,
        remark=payload.remark,
        conversion_id=None,
        commit=True,
    )

    return _build_transaction_response(transaction)


def list_transactions(
    db: Session,
    account_id: int,
    fund_code: str | None = None,
) -> list[FundHoldingTransactionResponse]:
    """查询账户下的持仓交易记录。"""
    if db.get(FundAccount, account_id) is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")

    stmt = select(FundTransaction).where(FundTransaction.account_id == account_id)
    if fund_code:
        stmt = stmt.where(FundTransaction.fund_code == str(fund_code).strip())
    transactions = db.execute(stmt.order_by(FundTransaction.id.desc())).scalars().all()

    return [_build_transaction_response(transaction) for transaction in transactions]


def confirm_pending_transactions(db: Session) -> int:
    """确认已到期的待确认交易。"""
    today = cst_now().date()
    transactions = (
        db.execute(
            select(FundTransaction).where(
                FundTransaction.status == FundTradeStatus.pending,
                FundTransaction.confirmed_nav_date <= today,
            )
        )
        .scalars()
        .all()
    )
    if not transactions:
        return 0

    updated = 0
    for transaction in transactions:
        holding = transaction.holding
        if holding is None:
            holding = (
                db.execute(
                    select(FundHolding).where(
                        FundHolding.account_id == transaction.account_id,
                        FundHolding.fund_code == transaction.fund_code,
                    )
                )
                .scalars()
                .first()
            )
        if holding is None:
            holding = FundHolding(
                account_id=transaction.account_id,
                fund_code=transaction.fund_code,
                total_amount=0.0,
                total_shares=0.0,
            )
            db.add(holding)
            db.flush()
            transaction.holding_id = holding.id

        _apply_holding_change(
            holding,
            transaction.trade_type,
            transaction.amount,
            transaction.shares,
        )
        transaction.status = FundTradeStatus.confirmed
        updated += 1

    db.commit()
    return updated


def _create_transaction_record(
    db: Session,
    account_id: int,
    fund_code: str,
    trade_type: FundTradeType,
    amount: float,
    fee_percent: float | None,
    confirmed_nav: float,
    trade_time: datetime | None,
    holding_amount: float | None,
    profit_amount: float | None,
    remark: str | None,
    conversion_id: int | None,
    commit: bool,
) -> FundTransaction:
    account = db.get(FundAccount, account_id)
    if account is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")

    resolved_fee_percent = fee_percent
    if resolved_fee_percent is None and trade_type == FundTradeType.buy:
        resolved_fee_percent = account.default_buy_fee_percent

    resolved_fund_code = str(fund_code).strip()
    holding = (
        db.execute(
            select(FundHolding).where(
                FundHolding.account_id == account_id,
                FundHolding.fund_code == resolved_fund_code,
            )
        )
        .scalars()
        .first()
    )

    if holding is None and trade_type == FundTradeType.sell:
        raise FundHoldingNotFoundError(f"未找到基金持仓: {resolved_fund_code}")
    if holding is None:
        holding = FundHolding(
            account_id=account_id,
            fund_code=resolved_fund_code,
            total_amount=0.0,
            total_shares=0.0,
        )
        db.add(holding)
        db.flush()

    fee_amount = amount * (resolved_fee_percent or 0.0) / 100
    payload = FundHoldingTransactionCreateRequest(
        account_id=account_id,
        fund_code=resolved_fund_code,
        trade_type=trade_type,
        amount=amount,
        fee_percent=resolved_fee_percent,
        confirmed_nav=confirmed_nav,
        trade_time=trade_time,
        holding_amount=holding_amount,
        profit_amount=profit_amount,
        remark=remark,
    )
    share_base_amount = _resolve_share_base_amount(payload, fee_amount)
    if share_base_amount <= 0:
        raise ValueError("份额计算基础金额必须大于 0")
    if confirmed_nav <= 0:
        raise ValueError("确认净值必须大于 0")

    shares = share_base_amount / confirmed_nav
    resolved_trade_time = ensure_cst(trade_time)
    confirmed_nav_date = _resolve_confirmed_nav_date(resolved_trade_time)
    status = _resolve_trade_status(confirmed_nav_date)

    if trade_type == FundTradeType.sell:
        if holding.total_amount < amount:
            raise ValueError("减仓金额不能超过当前持仓金额")
        if holding.total_shares < shares:
            raise ValueError("减仓份额不能超过当前持仓份额")

    if status == FundTradeStatus.confirmed:
        _apply_holding_change(holding, trade_type, amount, shares)

    transaction = FundTransaction(
        account_id=account_id,
        holding_id=holding.id,
        conversion_id=conversion_id,
        fund_code=resolved_fund_code,
        trade_type=trade_type,
        status=status,
        amount=amount,
        fee_percent=resolved_fee_percent or 0.0,
        fee_amount=fee_amount,
        confirmed_nav=confirmed_nav,
        confirmed_nav_date=confirmed_nav_date,
        shares=shares,
        holding_amount=holding_amount,
        profit_amount=profit_amount,
        trade_time=resolved_trade_time,
        remark=remark,
    )
    db.add(transaction)
    db.flush()
    if commit:
        db.commit()
        db.refresh(transaction)

    return transaction


def _build_transaction_response(
    transaction: FundTransaction,
) -> FundHoldingTransactionResponse:
    return FundHoldingTransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        holding_id=transaction.holding_id,
        conversion_id=transaction.conversion_id,
        fund_code=transaction.fund_code,
        trade_type=transaction.trade_type,
        status=transaction.status,
        amount=transaction.amount,
        fee_percent=transaction.fee_percent,
        fee_amount=transaction.fee_amount,
        confirmed_nav=transaction.confirmed_nav,
        confirmed_nav_date=transaction.confirmed_nav_date,
        shares=transaction.shares,
        holding_amount=transaction.holding_amount,
        profit_amount=transaction.profit_amount,
        trade_time=transaction.trade_time,
        remark=transaction.remark,
    )


def _resolve_share_base_amount(
    payload: FundHoldingTransactionCreateRequest,
    fee_amount: float,
) -> float:
    if (
        payload.trade_type == FundTradeType.buy
        and payload.holding_amount is not None
        and payload.profit_amount is not None
    ):
        return payload.holding_amount - payload.profit_amount - fee_amount
    return payload.amount - fee_amount


def _apply_holding_change(
    holding: FundHolding,
    trade_type: FundTradeType,
    amount: float,
    shares: float,
) -> None:
    if trade_type == FundTradeType.buy:
        holding.total_amount += amount
        holding.total_shares += shares
    else:
        holding.total_amount -= amount
        holding.total_shares -= shares
    if holding.total_amount < 0 or holding.total_shares < 0:
        raise ValueError("持仓金额或份额不能为负数")


def _resolve_confirmed_nav_date(trade_time: datetime | None) -> datetime.date:
    current = ensure_cst(trade_time)
    date_part = current.date()
    if _is_trading_day(date_part) and current.hour < 15:
        return date_part
    next_day = date_part + timedelta(days=1)
    while not _is_trading_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def _resolve_trade_status(confirmed_nav_date: datetime.date) -> FundTradeStatus:
    today = cst_now().date()
    if confirmed_nav_date > today:
        return FundTradeStatus.pending
    return FundTradeStatus.confirmed


def _is_trading_day(date_value: datetime.date) -> bool:
    return is_trading_day(date_value)
