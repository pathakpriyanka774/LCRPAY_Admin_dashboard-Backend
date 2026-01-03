
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, func
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def get_ist_time():
    return datetime.now(IST)

Base = declarative_base()

class IntPrimaryKeyMixin:
    """Mixin for integer primary key"""
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=get_ist_time, 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=get_ist_time, 
        onupdate=get_ist_time,
        server_default=func.now(),
        server_onupdate=func.now()
    )
