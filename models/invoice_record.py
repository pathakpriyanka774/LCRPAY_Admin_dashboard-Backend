from sqlalchemy import Column, Integer, String, DateTime, Boolean
from core.base import Base
from datetime import datetime

class InvoiceRecord(Base):
    __tablename__ = "invoice_records"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    # Store transaction data directly without foreign key constraints
    transaction_id = Column(Integer, nullable=True)  # Just for reference, not FK
    user_id = Column(Integer, nullable=True)  # Just for reference, not FK
    user_member_id = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    user_mobile = Column(String, nullable=False)
    user_address = Column(String, nullable=True)
    service_type = Column(String, nullable=False)
    amount = Column(String, nullable=False)
    reference_id = Column(String, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    exported = Column(Boolean, default=False, nullable=False)
    export_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<InvoiceRecord(id={self.id}, invoice_number='{self.invoice_number}', reference_id='{self.reference_id}')>"
