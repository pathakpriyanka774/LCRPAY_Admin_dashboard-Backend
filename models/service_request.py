from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any,List
# from typing import List, Optional, Dict, Any

from sqlalchemy import (
    VARCHAR,
    NUMERIC,
    JSON,
    TIMESTAMP,
    text,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base import Base, IntPrimaryKeyMixin
from models.models import User
from models.payment_gateway import Payment_Gateway  # import at bottom to avoid circular import


class Service_Request(IntPrimaryKeyMixin, Base):
    """
    Universal service request table to track any paid service action
    (Recharge, BBPS Bill, Prime Activation, etc.)
    """
    __tablename__ = "service_request"

    # =========================
    # BASE RELATION
    # =========================
    

    user_id: Mapped[int] = mapped_column(ForeignKey("users.UserID", ondelete="CASCADE"), index=True)
    
    # =========================
    # SERVICE DETAILS
    # =========================
    service_type: Mapped[str] = mapped_column(VARCHAR(30), index=True)
    """
    e.g. 'recharge', 'bbps', 'prime_activation', 'wallet_topup', etc.
    """

    operator_code: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    """
    For recharge/bbps use cases. Can be NULL for prime activation.
    """

    mobile_number: Mapped[Optional[str]] = mapped_column(VARCHAR(20))
    """
    Recharge or bill target. Can be NULL for prime activation.
    """

    # =========================
    # PAYMENT DETAILS
    # =========================
    amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    reference_id: Mapped[str] = mapped_column(VARCHAR(30), unique=True, index=True)
    """
    Unique client transaction ID used for linking SabPaisa callback.
    """

    status: Mapped[str] = mapped_column(
        VARCHAR(15),
        server_default=text("'pending'"),
        index=True
    )
    
    """
    'pending' | 'paid' | 'failed' | 'processing' | 'completed'
    """

    payment_txn_id: Mapped[Optional[str]] = mapped_column(VARCHAR(50), index=True)
    """
    SabPaisa transaction ID
    """

    utr_no: Mapped[Optional[str]] = mapped_column(VARCHAR(50), index=True)
    """
    Bank UTR / RRN
    """

    # =========================
    # ADDITIONAL / FLEXIBLE DATA
    # =========================
    service_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    """
    JSON field to store flexible service data (biller_id, plan_id, duration, etc.)
    """

    # =========================
    # TIMESTAMPS
    # =========================
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True
    )
    
    job_logs: Mapped[list["ServiceJobLog"]] = relationship(
        back_populates="service_request", cascade="all, delete-orphan", lazy="selectin"
    )
        
        
    

    # =========================
    # INDEX DEFINITIONS
    # =========================
    __table_args__ = (
        Index("ix_service_user_status", "user_id", "status"),
        Index("ix_service_type_status", "service_type", "status"),
        Index("ix_service_user_type", "user_id", "service_type"),
        Index("ix_service_ref_status", "reference_id", "status"),
    )

    # =========================
    # RELATIONSHIPS
    # =========================
    # user: Mapped["User"] = relationship(back_populates="service_requests")
    
    
    # payments: Mapped[List["Payment_Gateway"]] = relationship(
    #     back_populates="service_request",
    #     cascade="all, delete-orphan",
    #     lazy="selectin"
    # )
    
    payments: Mapped[list["Payment_Gateway"]] = relationship(
        back_populates="service_request",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<Service_Request(id={self.id}, user_id={self.user_id}, "
            f"service_type={self.service_type}, status={self.status}, "
            f"reference_id={self.reference_id})>"
        )








