"""Expense transaction record."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from iems.extensions import db
from iems.models.base import TimestampMixin


class ExpenseTransaction(TimestampMixin, db.Model):
    __tablename__ = "expense_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payee: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference_no: Mapped[str | None] = mapped_column(String(100))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
