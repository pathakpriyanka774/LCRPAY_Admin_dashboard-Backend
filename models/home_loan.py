from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from core.base import Base

class HomeLoan(Base):
    __tablename__ = "home_loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    loan_amount = Column(Float, nullable=False)
    property_value = Column(Float, nullable=False)
    income_continuity = Column(String(100), nullable=False)
    employment_status = Column(String(50), nullable=False)  # Residential, Commercial, Industrial
    user_mobile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)