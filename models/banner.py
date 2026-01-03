from sqlalchemy import Column, Integer, String, Date
from core.base import Base
class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    serial_no = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    navigation_url = Column(String, nullable=False)
    navigation_type = Column(String, nullable=False)  # 👈 New Field
    valid_till = Column(Date, nullable=False)