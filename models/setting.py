from sqlalchemy import (
    Column,
    Integer,
    Boolean,
)
from core.base import Base
# ================================Setting Table Come Here ===========================================================


class userSetting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    Referal = Column(Boolean, default=True)
    PhoneAutoCapture = Column(Boolean, default=True)