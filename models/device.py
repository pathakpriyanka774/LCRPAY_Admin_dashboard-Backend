# app/models/device.py
from __future__ import annotations
from sqlalchemy import VARCHAR, BOOLEAN, TIMESTAMP, Index, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from core.base import Base,IntPrimaryKeyMixin, TimestampMixin
# from models.mixins import IntPrimaryKeyMixin, TimestampMixin
from models.models import User

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

class Device(IntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "device"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.UserID", ondelete="CASCADE"), index=True)
    user: Mapped[User] = relationship(backref="devices")

    token: Mapped[str] = mapped_column(VARCHAR(255), unique=True, index=True, nullable=False)
    platform: Mapped[str] = mapped_column(VARCHAR(16), server_default=text("'android'"))  # 'android'|'ios'|'web'
    app_version: Mapped[str | None] = mapped_column(VARCHAR(32))
    is_active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False, server_default=text("true"))
    last_seen: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), index=True)

    __table_args__ = (Index("ix_device_user_active", "user_id", "is_active"),)