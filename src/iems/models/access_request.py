"""Pending account and password-recovery requests."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash

from iems.extensions import db
from iems.models.base import TimestampMixin, utc_now
from iems.models.user import Role


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class SignupRequest(TimestampMixin, db.Model):
    """An account request that must be approved before a User is created."""

    __tablename__ = "signup_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    requested_role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False, default=Role.TREASURER)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(SqlEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING, index=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)


class PasswordResetRequest(db.Model):
    """An internal request for an administrator to reset a user's password."""

    __tablename__ = "password_reset_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(SqlEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING, index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    handled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
