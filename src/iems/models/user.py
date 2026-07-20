"""Application users and roles."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, Enum as SqlEnum, String
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from iems.extensions import db
from iems.models.base import TimestampMixin


class Role(str, Enum):
    ADMIN = "admin"
    TREASURER = "treasurer"


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False, default=Role.TREASURER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
