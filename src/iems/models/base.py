"""Reusable database model helpers."""

from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Return a timezone-aware timestamp for audit fields."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Add consistent creation and update timestamps to an entity."""

    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
