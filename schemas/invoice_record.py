from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InvoiceRecordBase(BaseModel):
    invoice_number: str
    transaction_id: Optional[int] = None
    user_id: Optional[int] = None
    user_member_id: str
    user_name: str
    user_mobile: str
    user_address: Optional[str] = None
    service_type: str
    amount: str
    reference_id: str
    transaction_date: datetime
    exported: bool = False

class InvoiceRecordCreate(InvoiceRecordBase):
    pass

class InvoiceRecordResponse(InvoiceRecordBase):
    id: int
    invoice_date: datetime
    created_at: datetime
    export_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class InvoiceRecordUpdate(BaseModel):
    exported: Optional[bool] = None
    export_date: Optional[datetime] = None

class InvoiceNumberResponse(BaseModel):
    next_invoice_number: str
    prefix: str
    suffix: int
    year: int
    month: int
