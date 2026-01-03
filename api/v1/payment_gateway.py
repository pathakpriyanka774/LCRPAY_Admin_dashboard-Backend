
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from core.database import get_db
from models.payment_gateway import Payment_Gateway

router = APIRouter(tags=["payment-gateway"])


@router.get("/all")
async def get_all_payment_gateway_transactions(
    limit: int = Query(500, le=2000),
    status: str = Query(None),
    payment_mode: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get all payment gateway transactions with optional filters"""
    try:
        # Base query with optimized loading
        query = db.query(Payment_Gateway)
        
        # Apply filters if provided
        if status and status != 'all':
            query = query.filter(Payment_Gateway.status == status.upper())
        
        if payment_mode and payment_mode != 'all':
            query = query.filter(Payment_Gateway.payment_mode == payment_mode)
        
        # Order by latest first and limit results
        transactions = query.order_by(desc(Payment_Gateway.created_at)).limit(limit).all()

        result = []
        for txn in transactions:
            result.append({
                "id": txn.id,
                "client_txn_id": txn.client_txn_id,
                "sabpaisa_txn_id": txn.sabpaisa_txn_id or "N/A",
                "payer_name": txn.payer_name or "Unknown",
                "payer_email": txn.payer_email or "N/A",
                "payer_mobile": txn.payer_mobile,
                "amount": float(txn.amount) if txn.amount else 0.0,
                "paid_amount": float(txn.paid_amount) if txn.paid_amount else 0.0,
                "payment_mode": txn.payment_mode or "N/A",
                "bank_name": txn.bank_name or "N/A",
                "rrn": txn.rrn or "N/A",
                "purpose": txn.purpose or "N/A",
                "status": txn.status or "PENDING",
                "status_code": txn.status_code or "N/A",
                "sabpaisa_message": txn.sabpaisa_message or "N/A",
                "service_data": txn.service_data,
                "amount_type": txn.amount_type or "INR",
                "challan_number": txn.challan_number or "N/A",
                "bank_error_code": txn.bank_error_code or "N/A",
                "sabpaisa_error_code": txn.sabpaisa_error_code or "N/A",
                "trans_date": txn.trans_date.isoformat() if txn.trans_date else None,
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
                "updated_at": txn.updated_at.isoformat() if txn.updated_at else None,
                "service_request_id": txn.service_request_id
            })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statuses")
async def get_payment_statuses(db: Session = Depends(get_db)):
    """Get all unique payment statuses"""
    try:
        statuses = db.query(Payment_Gateway.status).distinct().all()
        return [s[0] for s in statuses if s[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-modes")
async def get_payment_modes(db: Session = Depends(get_db)):
    """Get all unique payment modes"""
    try:
        modes = db.query(Payment_Gateway.payment_mode).distinct().all()
        return [m[0] for m in modes if m[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
