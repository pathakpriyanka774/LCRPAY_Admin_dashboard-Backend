from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class DashboardStatsResponse(BaseModel):
    total_users: int = 0
    new_signups_today: int = 0
    new_signups_last_7_days: int = 0
    kyc_verified_users: int = 0
    verified_accounts: int = 0
    kyc_verification_percentage: float = 0.0
    prime_users: int = 0
    total_lcr_money: float = 0.0
    total_lcr_reward_distributed: float = 0.0
    total_payment_requests: int = 0
    total_distributor_lcr_money: float = 0.0
    total_distributor_prime_reward: float = 0.0
    total_mobile_recharge: int = 0
    total_dth_recharge: int = 0
    active_system_status: bool = True

    class Config:
        from_attributes = True

class DailyVolumeData(BaseModel):
    name: str
    transactions: int = 0
    amount: float = 0.0

class ServiceDistributionData(BaseModel):
    name: str
    value: float = 0.0
    color: str = "#9ca3af"

class ChartDataResponse(BaseModel):
    daily_volume: List[DailyVolumeData] = []
    service_distribution: List[ServiceDistributionData] = []

class LiveTransactionResponse(BaseModel):
    id: str = "N/A"
    user: str = "Unknown"
    service: str = "N/A"
    amount: float = 0.0
    status: str = "Pending"
    location: str = "India"

class RecentUserResponse(BaseModel):
    id: str = "0"
    name: str = "Unknown"
    email: str = ""
    mobile: str = ""
    role: str = "Retailer"
    location: str = "India"
    device: str = "Desktop"
    registered_at: str = ""

class TransactionDetailResponse(BaseModel):
    id: str
    user: str
    service: str
    amount: float
    status: str
    date: datetime
    reference_id: str

class ComplaintResponse(BaseModel):
    id: str
    user: str
    txn_id: str
    issue_type: str
    status: str
    submitted_on: datetime
    description: str