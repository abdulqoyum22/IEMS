"""Income and expense categories."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, Enum as SqlEnum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from iems.extensions import db
from iems.models.base import TimestampMixin


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(TimestampMixin, db.Model):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", "category_type", name="uq_category_name_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[CategoryType] = mapped_column(SqlEnum(CategoryType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
