
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from sqlalchemy import text

router = APIRouter(tags=["test"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Backend API is running"
    }

@router.get("/db-test")
async def test_database(db: Session = Depends(get_db)):
    """Test database connection"""
    try:
        # Test connection
        result = db.execute(text("SELECT 1")).scalar()
        
        # Count users
        user_count = db.execute(text('SELECT COUNT(*) FROM users WHERE "IsDeleted" = FALSE')).scalar()
        
        # Count transactions
        txn_count = db.execute(text("SELECT COUNT(*) FROM payment_gateway")).scalar()
        
        return {
            "status": "success",
            "connection": "active",
            "test_query": result,
            "total_users": user_count,
            "total_transactions": txn_count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
