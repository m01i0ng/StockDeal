from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import FundAccountNotFoundError, FundHoldingNotFoundError
from app.models.db.models import FundAccount, FundHolding, FundTransaction
from app.models.enums import FundTradeStatus, FundTradeType
from app.models.schemas import (
    FundHoldingCreateRequest,
    FundHoldingPositionResponse,
    FundHoldingTransactionCreateRequest,
    FundHoldingTransactionResponse,
    FundHoldingUpdateRequest,
)
from app.services.fund import fund_service
from app.services.trading_calendar import is_trading_day
from app.time_utils import cst_now, ensure_cst
from app.utils.parsing import parse_float


def create_holding(
    db: Session,
    payload: FundHoldingCreateRequest,
) -> FundHoldingTransactionResponse:
    """添加持仓并生成确认交易记录。"""
    account = db.get(FundAccount, payload.account_id)
    if account is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {payload.account_id}")

    resolved_fund_code = str(payload.fund_code).strip()
    existing = (
        db.execute(
            select(FundHolding).where(
                FundHolding.account_id == payload.account_id,
                FundHolding.fund_code == resolved_fund_code,
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        raise ValueError("持仓已存在")

    snapshot = fund_service.get_fund_snapshot(resolved_fund_code)
    confirmed_nav = float(snapshot.nav.nav)
    confirmed_nav_date = _ensure_date(snapshot.nav.date)
    if confirmed_nav <= 0:
        raise ValueError("确认净值必须大于 0")

    holding_amount = payload.total_amount + payload.profit_amount
    if holding_amount <= 0:
        raise ValueError("持仓总额必须大于 0")
    shares = holding_amount / confirmed_nav

    holding = FundHolding(
        account_id=payload.account_id,
        fund_code=resolved_fund_code,
        total_amount=payload.total_amount,
        total_shares=shares,
    )
    db.add(holding)
    db.flush()

    transaction = FundTransaction(
        account_id=payload.account_id,
        holding_id=holding.id,
        conversion_id=None,
        fund_code=resolved_fund_code,
        trade_type=FundTradeType.buy,
        status=FundTradeStatus.confirmed,
        amount=payload.total_amount,
        fee_percent=0.0,
        fee_amount=0.0,
        confirmed_nav=confirmed_nav,
        confirmed_nav_date=confirmed_nav_date,
        shares=shares,
        holding_amount=holding_amount,
        profit_amount=payload.profit_amount,
        trade_time=_resolve_trade_time(confirmed_nav_date, False),
        remark=payload.remark,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return _build_transaction_response(transaction)


def get_holding_detail(
    db: Session,
    holding_id: int,
) -> FundHoldingPositionResponse:
    """获取持仓详情。"""
    holding = db.get(FundHolding, holding_id)
    if holding is None:
        raise FundHoldingNotFoundError(f"未找到基金持仓: {holding_id}")
    return _build_holding_position(holding)


def update_holding(
    db: Session,
    holding_id: int,
    payload: FundHoldingUpdateRequest,
) -> FundHoldingPositionResponse:
    """更新持仓信息。"""
    holding = db.get(FundHolding, holding_id)
    if holding is None:
        raise FundHoldingNotFoundError(f"未找到基金持仓: {holding_id}")
    if payload.total_amount < 0 or payload.total_shares < 0:
        raise ValueError("持仓金额或份额不能为负数")

    holding.total_amount = payload.total_amount
    holding.total_shares = payload.total_shares
    db.commit()
    db.refresh(holding)
    return _build_holding_position(holding)


def delete_holding(db: Session, holding_id: int) -> None:
    """删除持仓记录。"""
    holding = db.get(FundHolding, holding_id)
    if holding is None:
        raise FundHoldingNotFoundError(f"未找到基金持仓: {holding_id}")
    db.delete(holding)
    db.commit()


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
        trade_date=payload.trade_date,
        is_after_cutoff=payload.is_after_cutoff,
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

        fee_amount = transaction.amount * transaction.fee_percent / 100
        share_base_amount = transaction.amount - fee_amount
        if share_base_amount <= 0:
            raise ValueError("份额计算基础金额必须大于 0")

        confirmed_nav = fund_service.resolve_fund_nav_by_date(
            transaction.fund_code,
            transaction.confirmed_nav_date,
        )
        if confirmed_nav <= 0:
            raise ValueError("确认净值必须大于 0")

        shares = share_base_amount / confirmed_nav

        if transaction.trade_type == FundTradeType.sell:
            if holding.total_amount < transaction.amount:
                raise ValueError("减仓金额不能超过当前持仓金额")
            if holding.total_shares < shares:
                raise ValueError("减仓份额不能超过当前持仓份额")

        transaction.confirmed_nav = confirmed_nav
        transaction.shares = shares

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
    trade_date: datetime.date,
    is_after_cutoff: bool,
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
    share_base_amount = amount - fee_amount
    if share_base_amount <= 0:
        raise ValueError("份额计算基础金额必须大于 0")

    confirmed_nav_date = _resolve_confirmed_nav_date(trade_date, is_after_cutoff)
    status = _resolve_trade_status(confirmed_nav_date)
    resolved_trade_time = _resolve_trade_time(trade_date, is_after_cutoff)

    confirmed_nav = 0.0
    shares = 0.0
    if status == FundTradeStatus.confirmed:
        confirmed_nav = fund_service.resolve_fund_nav_by_date(
            resolved_fund_code, confirmed_nav_date
        )
        if confirmed_nav <= 0:
            raise ValueError("确认净值必须大于 0")
        shares = share_base_amount / confirmed_nav

        if trade_type == FundTradeType.sell:
            if holding.total_amount < amount:
                raise ValueError("减仓金额不能超过当前持仓金额")
            if holding.total_shares < shares:
                raise ValueError("减仓份额不能超过当前持仓份额")

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


def _ensure_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


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


def _resolve_confirmed_nav_date(
    trade_date: datetime.date,
    is_after_cutoff: bool,
) -> datetime.date:
    if _is_trading_day(trade_date) and not is_after_cutoff:
        return trade_date
    next_day = trade_date + timedelta(days=1)
    while not _is_trading_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def _resolve_trade_time(
    trade_date: datetime.date,
    is_after_cutoff: bool,
) -> datetime:
    cutoff_time = time(15, 1) if is_after_cutoff else time(14, 59)
    return ensure_cst(datetime.combine(trade_date, cutoff_time))


def _resolve_trade_status(confirmed_nav_date: datetime.date) -> FundTradeStatus:
    today = cst_now().date()
    if confirmed_nav_date > today:
        return FundTradeStatus.pending
    return FundTradeStatus.confirmed


def _is_trading_day(date_value: datetime.date) -> bool:
    return is_trading_day(date_value)
