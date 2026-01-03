from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any,List

from sqlalchemy import (
    VARCHAR,
    NUMERIC,
    JSON,
    TIMESTAMP,
    text,
    Index,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base import Base, IntPrimaryKeyMixin


class Payment_Gateway(IntPrimaryKeyMixin, Base):
    """
    Stores all SabPaisa payment transactions for any service
    (Recharge, Prime Activation, BBPS, Wallet Recharge, etc.)
    Each payment links to a Service_Request entry.
    """
    __tablename__ = "payment_gateway"

    # =========================
    # RELATION TO SERVICE REQUEST
    # =========================
    # service_request_id: Mapped[int | None] = mapped_column(
    #     ForeignKey("service_request.id", ondelete="SET NULL"),
    #     nullable=True,
    #     index=True
    # )
    
    service_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_request.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Relationship - uses lazy loading, won't auto-join unless explicitly accessed
    service_request: Mapped["Service_Request"] = relationship(
        back_populates="payments",
        lazy="select"  # Changed from selectin to select for better performance
    )

    # =========================
    # BASIC PAYER INFO
    # =========================
    payer_name: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    payer_email: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    payer_mobile: Mapped[str] = mapped_column(VARCHAR(20), index=True)

    # =========================
    # TRANSACTION DETAILS
    # =========================
    client_txn_id: Mapped[str] = mapped_column(VARCHAR(50), unique=True, index=True)
    sabpaisa_txn_id: Mapped[Optional[str]] = mapped_column(VARCHAR(50), index=True)
    amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    paid_amount: Mapped[Optional[Decimal]] = mapped_column(NUMERIC(10, 2))
    payment_mode: Mapped[Optional[str]] = mapped_column(VARCHAR(20))
    bank_name: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    rrn: Mapped[Optional[str]] = mapped_column(VARCHAR(50), index=True)  # UTR / RRN

    # =========================
    # STATUS & PURPOSE
    # =========================
    purpose: Mapped[Optional[str]] = mapped_column(VARCHAR(50), index=True)
    status: Mapped[str] = mapped_column(VARCHAR(20), server_default=text("'PENDING'"), index=True)
    status_code: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    sabpaisa_message: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

    # =========================
    # EXTRA / AUDIT INFO
    # =========================
    service_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    amount_type: Mapped[Optional[str]] = mapped_column(VARCHAR(5), default="INR")
    challan_number: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
    bank_error_code: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    sabpaisa_error_code: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
    trans_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), index=True)

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

    # =========================
    # RELATIONSHIPS
    # =========================
    # service_request: Mapped["Service_Request"] = relationship(
    #     back_populates="payments",
    #     lazy="selectin"
    # )
    
    # payments: Mapped[List["Payment_Gateway"]] = relationship(back_populates="service_request")


    # =========================
    # INDEXES
    # =========================
    __table_args__ = (
        Index("ix_pg_mobile_status", "payer_mobile", "status"),
        Index("ix_pg_service_status", "service_request_id", "status"),
        Index("ix_pg_purpose_status", "purpose", "status"),
        Index("ix_pg_created_status", "created_at", "status"),
    )

    def __repr__(self) -> str:
        return f"<Payment_Gateway(client_txn_id={self.client_txn_id}, status={self.status}, service_request_id={self.service_request_id})>"













# from __future__ import annotations
# from datetime import datetime
# from decimal import Decimal
# from typing import Optional, Dict, Any
# from sqlalchemy import VARCHAR, BOOLEAN, TIMESTAMP, Index, ForeignKey, text,NUMERIC,JSON


# from sqlalchemy.orm import Mapped, mapped_column
# from core.base import Base, IntPrimaryKeyMixin, TimestampMixin
# from models.models import User
# from models.service_request import Service_Request


# class Payment_Gateway(IntPrimaryKeyMixin, Base):
#     """
#     Stores all SabPaisa payment transactions for any service
#     (Recharge, Prime Activation, BBPS, Wallet Recharge, etc.)
#     """
#     __tablename__ = "payment_gateway"

#     # Basic payer info
    
#     service_request_id: Mapped[int | None] = mapped_column(
#         ForeignKey("service_request.id", ondelete="SET NULL"),
#         nullable=True,
#         index=True
#     )
#     user_id: Mapped[int] = mapped_column(ForeignKey("users.UserID", ondelete="CASCADE"), index=True)
#     payer_name: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
#     payer_email: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
#     payer_mobile: Mapped[str] = mapped_column(VARCHAR(20), index=True)

#     # Transaction details
#     client_txn_id: Mapped[str] = mapped_column(VARCHAR(50), unique=True, index=True)
#     sabpaisa_txn_id: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
#     amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
#     paid_amount: Mapped[Optional[Decimal]] = mapped_column(NUMERIC(10, 2))
#     payment_mode: Mapped[Optional[str]] = mapped_column(VARCHAR(20))
#     bank_name: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
#     rrn: Mapped[Optional[str]] = mapped_column(VARCHAR(50))  # Bank reference number (UTR)

#     # Status & purpose
#     purpose: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
#     status: Mapped[str] = mapped_column(VARCHAR(20), server_default=text("'PENDING'"))
#     status_code: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
#     sabpaisa_message: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

#     # Extra info / audit
#     service_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
#     amount_type: Mapped[Optional[str]] = mapped_column(VARCHAR(5), default="INR")
#     challan_number: Mapped[Optional[str]] = mapped_column(VARCHAR(50))
#     bank_error_code: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
#     sabpaisa_error_code: Mapped[Optional[str]] = mapped_column(VARCHAR(10))
#     trans_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

#     # Timestamps
#     created_at: Mapped[datetime] = mapped_column(
#         TIMESTAMP(timezone=True), default=datetime.utcnow
#     )
    
#     __table_args__ = (
#         # Composite indexes for most common queries
#         Index("ix_pg_mobile_status", "payer_mobile", "status"),
#         Index("ix_pg_purpose_status", "purpose", "status"),
#         Index("ix_pg_created_status", "created_at", "status"),
#         Index("ix_pg_user_purpose_time", "payer_mobile", "purpose", "created_at"),
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         TIMESTAMP(timezone=True),
#         default=datetime.utcnow,
#         onupdate=datetime.utcnow,
#     )

#     def __repr__(self) -> str:
#         return f"<Payment_Gateway(client_txn_id={self.client_txn_id}, status={self.status}, purpose={self.purpose})>"
