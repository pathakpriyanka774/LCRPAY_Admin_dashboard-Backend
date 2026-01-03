from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from core.base import Base

class MachineLoan(Base):
    __tablename__ = "machine_loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    business_name = Column(String(100), nullable=False)
    machine_type = Column(String(100), nullable=False)
    machine_cost = Column(Float, nullable=False)
    loan_amount = Column(Float, nullable=False)
    business_continuity = Column(Integer, nullable=False)
    co_applicant = Column(String(100), nullable=True)
    user_mobile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)