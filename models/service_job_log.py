from datetime import datetime
from sqlalchemy import VARCHAR, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base import Base, IntPrimaryKeyMixin


class ServiceJobLog(IntPrimaryKeyMixin, Base):
    """
    Logs background service executions after payment success
    (Recharge, D2H, BBPS, Prime activation, etc.)
    """
    __tablename__ = "service_job_log"

    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_request.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[str] = mapped_column(VARCHAR(30), index=True)  # recharge / d2h / bbps / prime
    status: Mapped[str] = mapped_column(VARCHAR(20), server_default=text("'pending'"))  # pending / running / success / failed
    message: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, index=True
    )

    service_request = relationship("Service_Request", back_populates="job_logs")