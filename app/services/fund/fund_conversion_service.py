from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import FundAccountNotFoundError
from app.models.db.models import FundAccount, FundConversion, FundTransaction
from app.models.enums import FundTradeType
from app.models.schemas import FundConversionCreateRequest, FundConversionResponse
from app.services.fund import fund_holding_service


def create_conversion(
    db: Session,
    payload: FundConversionCreateRequest,
) -> FundConversionResponse:
    """创建基金转换记录并生成买卖交易。"""
    account = db.get(FundAccount, payload.account_id)
    if account is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {payload.account_id}")

    trade_time = fund_holding_service._resolve_trade_time(
        payload.trade_date,
        payload.is_after_cutoff,
    )
    conversion = FundConversion(
        account_id=payload.account_id,
        from_fund_code=str(payload.from_fund_code).strip(),
        to_fund_code=str(payload.to_fund_code).strip(),
        trade_time=trade_time,
        remark=payload.remark,
    )
    db.add(conversion)
    db.flush()

    from_transaction = fund_holding_service._create_transaction_record(
        db=db,
        account_id=payload.account_id,
        fund_code=payload.from_fund_code,
        trade_type=FundTradeType.sell,
        amount=payload.from_amount,
        fee_percent=payload.from_fee_percent,
        trade_date=payload.trade_date,
        is_after_cutoff=payload.is_after_cutoff,
        remark=payload.remark,
        conversion_id=conversion.id,
        commit=False,
    )
    to_transaction = fund_holding_service._create_transaction_record(
        db=db,
        account_id=payload.account_id,
        fund_code=payload.to_fund_code,
        trade_type=FundTradeType.buy,
        amount=payload.to_amount,
        fee_percent=payload.to_fee_percent,
        trade_date=payload.trade_date,
        is_after_cutoff=payload.is_after_cutoff,
        remark=payload.remark,
        conversion_id=conversion.id,
        commit=False,
    )

    db.commit()
    db.refresh(conversion)
    db.refresh(from_transaction)
    db.refresh(to_transaction)

    return FundConversionResponse(
        id=conversion.id,
        account_id=conversion.account_id,
        from_fund_code=conversion.from_fund_code,
        to_fund_code=conversion.to_fund_code,
        trade_time=conversion.trade_time,
        remark=conversion.remark,
        created_at=conversion.created_at,
        from_transaction=fund_holding_service._build_transaction_response(
            from_transaction
        ),
        to_transaction=fund_holding_service._build_transaction_response(to_transaction),
    )


def list_conversions(db: Session, account_id: int) -> list[FundConversionResponse]:
    """查询账户下的基金转换记录。"""
    if db.get(FundAccount, account_id) is None:
        raise FundAccountNotFoundError(f"未找到基金账户: {account_id}")

    stmt = select(FundConversion).where(FundConversion.account_id == account_id)
    conversions = db.execute(stmt.order_by(FundConversion.id.desc())).scalars().all()

    responses: list[FundConversionResponse] = []
    for conversion in conversions:
        from_transaction, to_transaction = _resolve_conversion_transactions(
            conversion.transactions
        )
        responses.append(
            FundConversionResponse(
                id=conversion.id,
                account_id=conversion.account_id,
                from_fund_code=conversion.from_fund_code,
                to_fund_code=conversion.to_fund_code,
                trade_time=conversion.trade_time,
                remark=conversion.remark,
                created_at=conversion.created_at,
                from_transaction=fund_holding_service._build_transaction_response(
                    from_transaction
                ),
                to_transaction=fund_holding_service._build_transaction_response(
                    to_transaction
                ),
            )
        )

    return responses


def _resolve_conversion_transactions(
    transactions: list[FundTransaction],
) -> tuple[FundTransaction, FundTransaction]:
    from_transaction = next(
        (tx for tx in transactions if tx.trade_type == FundTradeType.sell),
        None,
    )
    to_transaction = next(
        (tx for tx in transactions if tx.trade_type == FundTradeType.buy),
        None,
    )
    if from_transaction is None or to_transaction is None:
        raise ValueError("转换记录缺少买入或卖出交易")
    return from_transaction, to_transaction
