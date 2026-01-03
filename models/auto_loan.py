from sqlalchemy import Column, String, Numeric, Integer, DateTime, Float
from datetime import datetime
from core.base import Base

class AutoLoan(Base):
    __tablename__ = "auto_loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    vehicle_type = Column(String(10), nullable=False)  # new / used
    vehicle_value = Column(Float, nullable=False)
    emis_paid = Column(Integer, nullable=True)
    user_mobile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)