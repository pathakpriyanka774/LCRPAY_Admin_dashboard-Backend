from sqlalchemy import Column, String, Numeric, Integer, DateTime, Float
from datetime import datetime
from core.base import Base

class PrivateFunding(Base):
    __tablename__ = "private_funding_applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    loan_amount = Column(Float, nullable=False)
    annual_turnover = Column(Float, nullable=False)
    employment_type = Column(String(10), nullable=False)  # SEP or SENP
    funding_purpose = Column(String(255), nullable=False)
    user_mobile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)