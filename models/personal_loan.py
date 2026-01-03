from sqlalchemy import Column, String, Numeric, Integer, DateTime, Float
from datetime import datetime
from core.base import Base

class PersonalLoan(Base):
    __tablename__ = "personal_loan_applications"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False)
    employment_status = Column(String(20), nullable=False)  # salaried / self-employed
    company_name = Column(String(100), nullable=True)
    monthly_income = Column(Float, nullable=False)
    existing_emis = Column(Float, nullable=True)
    loan_amount = Column(Float, nullable=False)
    tenure = Column(Integer, nullable=False)
    cibil_score = Column(Integer, nullable=False)
    user_mobile = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)