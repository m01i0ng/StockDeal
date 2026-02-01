from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.db import Base
from app.models.enums import FundTradeStatus, FundTradeType
from app.time_utils import cst_now


class FundAccount(Base):
    """基金账户。"""

    __tablename__ = "fund_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_buy_fee_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cst_now)

    holdings: Mapped[list["FundHolding"]] = relationship(
        "FundHolding",
        back_populates="account",
        cascade="all, delete-orphan",
        primaryjoin="FundAccount.id==foreign(FundHolding.account_id)",
    )
    transactions: Mapped[list["FundTransaction"]] = relationship(
        "FundTransaction",
        back_populates="account",
        cascade="all, delete-orphan",
        primaryjoin="FundAccount.id==foreign(FundTransaction.account_id)",
    )
    conversions: Mapped[list["FundConversion"]] = relationship(
        "FundConversion",
        back_populates="account",
        cascade="all, delete-orphan",
        primaryjoin="FundAccount.id==foreign(FundConversion.account_id)",
    )


class FundHolding(Base):
    """基金持仓。"""

    __tablename__ = "fund_holdings"
    __table_args__ = (
        UniqueConstraint("account_id", "fund_code", name="uniq_account_fund"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fund_code: Mapped[str] = mapped_column(String(32), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_shares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=cst_now, onupdate=cst_now
    )

    account: Mapped["FundAccount"] = relationship(
        "FundAccount",
        back_populates="holdings",
        primaryjoin="FundAccount.id==foreign(FundHolding.account_id)",
    )
    transactions: Mapped[list["FundTransaction"]] = relationship(
        "FundTransaction",
        back_populates="holding",
        cascade="all, delete-orphan",
        primaryjoin="FundHolding.id==foreign(FundTransaction.holding_id)",
    )


class FundConversion(Base):
    """基金转换记录。"""

    __tablename__ = "fund_conversions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_fund_code: Mapped[str] = mapped_column(String(32), nullable=False)
    to_fund_code: Mapped[str] = mapped_column(String(32), nullable=False)
    trade_time: Mapped[datetime] = mapped_column(DateTime, default=cst_now)
    remark: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cst_now)

    account: Mapped["FundAccount"] = relationship(
        "FundAccount",
        back_populates="conversions",
        primaryjoin="FundAccount.id==foreign(FundConversion.account_id)",
    )
    transactions: Mapped[list["FundTransaction"]] = relationship(
        "FundTransaction",
        back_populates="conversion",
        cascade="all, delete-orphan",
        primaryjoin="FundConversion.id==foreign(FundTransaction.conversion_id)",
    )


class FundTransaction(Base):
    """基金交易记录。"""

    __tablename__ = "fund_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    holding_id: Mapped[int | None] = mapped_column(Integer)
    conversion_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fund_code: Mapped[str] = mapped_column(String(32), nullable=False)
    trade_type: Mapped[FundTradeType] = mapped_column(
        Enum(FundTradeType), nullable=False
    )
    status: Mapped[FundTradeStatus] = mapped_column(
        Enum(FundTradeStatus), nullable=False, default=FundTradeStatus.confirmed
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    fee_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fee_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confirmed_nav: Mapped[float] = mapped_column(Float, nullable=False)
    confirmed_nav_date: Mapped[dt_date] = mapped_column(Date, nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    holding_amount: Mapped[float | None] = mapped_column(Float)
    profit_amount: Mapped[float | None] = mapped_column(Float)
    trade_time: Mapped[datetime] = mapped_column(DateTime, default=cst_now)
    remark: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=cst_now)

    account: Mapped["FundAccount"] = relationship(
        "FundAccount",
        back_populates="transactions",
        primaryjoin="FundAccount.id==foreign(FundTransaction.account_id)",
    )
    holding: Mapped[Optional["FundHolding"]] = relationship(
        "FundHolding",
        back_populates="transactions",
        primaryjoin="FundHolding.id==foreign(FundTransaction.holding_id)",
    )
    conversion: Mapped[Optional["FundConversion"]] = relationship(
        "FundConversion",
        back_populates="transactions",
        primaryjoin="FundConversion.id==foreign(FundTransaction.conversion_id)",
    )
