# app/models/push_token.py
from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from core.base import Base,IntPrimaryKeyMixin, TimestampMixin

from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey
import enum

class PlatformEnum(str, enum.Enum):
    android = "android"
    ios = "ios"
    web = "web"

class PushToken(IntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "push_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.UserID", ondelete="CASCADE"), index=True, nullable=False
    )
    # user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    platform: Mapped[PlatformEnum] = mapped_column(Enum(PlatformEnum), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(255))
    app_version: Mapped[str | None] = mapped_column(String(64))
    sdk: Mapped[str | None] = mapped_column(String(64))  # e.g., 'react-native-firebase'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
