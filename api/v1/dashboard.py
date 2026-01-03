from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from decimal import Decimal
from core.database import get_db
from core.auth import get_current_user, TokenData
from services.dashboard_service import DashboardService
from models.models import User
from schemas.dashboard import (
    DashboardStatsResponse,
    ChartDataResponse,
    LiveTransactionResponse,
    RecentUserResponse
)

router = APIRouter(tags=["dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard statistics"""
    try:
        # Total Prime Users
        total_prime_users = db.query(func.count(User.UserID)).filter(
            User.IsDeleted == False,
            User.prime_status == True
        ).scalar() or 0

        # Total LCR Money
        from models.models import LcrMoney
        total_lcr_money = db.query(func.sum(LcrMoney.amount)).filter(
            LcrMoney.status == 1
        ).scalar() or Decimal("0.00")

        # Total LCR Rewards
        from models.models import LcrRewards
        total_lcr_rewards = db.query(func.sum(LcrRewards.amount)).filter(
            LcrRewards.status == 1
        ).scalar() or Decimal("0.00")

        stats = DashboardService.get_dashboard_stats(db)
        return DashboardStatsResponse(**stats)
    except Exception as e:
        error_msg = str(e).lower()
        if 'database' in error_msg or 'connection' in error_msg or 'operational' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please check your .env configuration."
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/charts", response_model=ChartDataResponse)
async def get_chart_data(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chart data for daily volume and service distribution"""
    try:
        charts = DashboardService.get_chart_data(db)
        return ChartDataResponse(**charts)
    except Exception as e:
        error_msg = str(e).lower()
        if 'database' in error_msg or 'connection' in error_msg or 'operational' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please check your .env configuration."
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def get_transactions(
    current_user: TokenData = Depends(get_current_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get transactions with total count"""
    try:
        result = DashboardService.get_live_transactions(db, limit)
        return result
    except Exception as e:
        error_msg = str(e).lower()
        if 'database' in error_msg or 'connection' in error_msg or 'operational' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please check your .env configuration."
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/recent", response_model=List[RecentUserResponse])
async def get_recent_users(
    current_user: TokenData = Depends(get_current_user),
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recently registered users"""
    try:
        users = DashboardService.get_recent_users(db, limit)
        return users
    except Exception as e:
        error_msg = str(e).lower()
        if 'database' in error_msg or 'connection' in error_msg or 'operational' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please check your .env configuration."
            )
        raise HTTPException(status_code=500, detail=str(e))