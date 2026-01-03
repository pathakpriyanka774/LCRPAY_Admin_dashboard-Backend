from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from core.base import Base

class ServiceRegistration(Base):
    __tablename__ = "service_registration"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, nullable=False)  # 👈 current_user ka mobile
    service_type = Column(String, nullable=False)  # e.g., "Skill Development"
    registered_at = Column(DateTime, default=datetime.utcnow)  #⏱️ timestamp