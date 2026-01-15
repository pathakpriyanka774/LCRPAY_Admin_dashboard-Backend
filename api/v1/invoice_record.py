from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional

from core.database import get_db
from models.invoice_record import InvoiceRecord
from schemas.invoice_record import InvoiceRecordCreate, InvoiceRecordResponse, InvoiceNumberResponse

router = APIRouter(tags=["invoices"])

@router.get("/next-number/{transaction_date}", response_model=InvoiceNumberResponse)
def get_next_invoice_number(
    transaction_date: str,
    reference_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Generate next invoice number based on transaction date and existing records.
    If reference_id is provided, checks for existing invoice with that reference first."""
    try:
        # Parse transaction date (expected format: YYYY-MM-DD or any ISO format)
        try:
            trans_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
        except ValueError:
            # Try common formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y']:
                try:
                    trans_date = datetime.strptime(transaction_date, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY"
                )
        
        # If reference_id is provided, check for existing invoice first
        if reference_id:
            existing_invoice = db.query(InvoiceRecord).filter(
                InvoiceRecord.reference_id == reference_id
            ).first()
            
            if existing_invoice:
                # Return the existing invoice number
                existing_number = existing_invoice.invoice_number
                # Extract prefix and suffix from existing number for consistency
                if len(existing_number) >= 11:  # LCR + YYYYMM + 4 digits
                    prefix = existing_number[:9]  # LCR + YYYYMM
                    suffix = existing_number[9:]  # numeric part
                    try:
                        suffix_int = int(suffix)
                        year = int(existing_number[3:7])  # Extract YYYY
                        month = int(existing_number[7:9])  # Extract MM
                        return {
                            "next_invoice_number": existing_number,
                            "prefix": prefix,
                            "suffix": suffix_int,
                            "year": year,
                            "month": month
                        }
                    except ValueError:
                        pass  # Fall through to generate new number if parsing fails
        
        # Extract year and month
        year = trans_date.year
        month = trans_date.month
        
        # Generate prefix: LCR + YYYY + MM (zero-padded)
        prefix = f"LCR{year}{month:02d}"
        
        # Find the highest existing invoice number for this year and month
        latest_invoice = db.query(InvoiceRecord).filter(
            InvoiceRecord.invoice_number.like(f"{prefix}%")
        ).order_by(InvoiceRecord.invoice_number.desc()).first()
        
        if latest_invoice:
            # Extract the numeric part and increment
            current_number = latest_invoice.invoice_number
            numeric_part = current_number[len(prefix):]
            try:
                next_suffix = int(numeric_part) + 1
            except ValueError:
                next_suffix = 1
        else:
            next_suffix = 1
        
        # Generate next invoice number with 4-digit padding
        next_invoice_number = f"{prefix}{next_suffix:04d}"
        
        return {
            "next_invoice_number": next_invoice_number,
            "prefix": prefix,
            "suffix": next_suffix,
            "year": year,
            "month": month
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate invoice number: {str(e)}"
        )

@router.post("/record", response_model=InvoiceRecordResponse)
def create_invoice_record(
    invoice_data: InvoiceRecordCreate,
    db: Session = Depends(get_db)
):
    """Create a new invoice record"""
    try:
        # Check if invoice number already exists
        existing_invoice = db.query(InvoiceRecord).filter(
            InvoiceRecord.invoice_number == invoice_data.invoice_number
        ).first()
        
        if existing_invoice:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice number already exists"
            )
        
        # Check if transaction exists, if not, create a dummy record or make it nullable
        # For now, we'll proceed with the record even if transaction doesn't exist
        # This allows invoice generation without strict foreign key constraints
        
        # Create new invoice record
        invoice_record = InvoiceRecord(
            invoice_number=invoice_data.invoice_number,
            transaction_id=invoice_data.transaction_id,
            user_id=invoice_data.user_id,
            user_member_id=invoice_data.user_member_id,
            user_name=invoice_data.user_name,
            user_mobile=invoice_data.user_mobile,
            user_address=invoice_data.user_address,
            service_type=invoice_data.service_type,
            amount=invoice_data.amount,
            reference_id=invoice_data.reference_id,
            transaction_date=invoice_data.transaction_date,
            exported=invoice_data.exported
        )
        
        db.add(invoice_record)
        db.commit()
        db.refresh(invoice_record)
        
        return invoice_record
        
    except Exception as e:
        db.rollback()
        # Log the full error for debugging
        print(f"Error creating invoice record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice record: {str(e)}"
        )

@router.put("/{invoice_id}/export")
def mark_invoice_exported(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Mark an invoice as exported"""
    try:
        invoice_record = db.query(InvoiceRecord).filter(
            InvoiceRecord.id == invoice_id
        ).first()
        
        if not invoice_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice record not found"
            )
        
        invoice_record.exported = True
        invoice_record.export_date = datetime.utcnow()
        
        db.commit()
        db.refresh(invoice_record)
        
        return {"message": "Invoice marked as exported successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark invoice as exported: {str(e)}"
        )

@router.get("/transaction/{transaction_id}", response_model=Optional[InvoiceRecordResponse])
def get_invoice_by_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Get invoice record by transaction ID"""
    try:
        invoice_record = db.query(InvoiceRecord).filter(
            InvoiceRecord.transaction_id == transaction_id
        ).first()
        
        return invoice_record
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice record: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[InvoiceRecordResponse])
def get_invoices_by_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all invoice records for a specific user"""
    try:
        invoice_records = db.query(InvoiceRecord).filter(
            InvoiceRecord.user_id == user_id
        ).order_by(InvoiceRecord.created_at.desc()).all()
        
        return invoice_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice records: {str(e)}"
        )

@router.get("/", response_model=List[InvoiceRecordResponse])
def get_all_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all invoice records with pagination"""
    try:
        invoice_records = db.query(InvoiceRecord).order_by(
            InvoiceRecord.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return invoice_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice records: {str(e)}"
        )
