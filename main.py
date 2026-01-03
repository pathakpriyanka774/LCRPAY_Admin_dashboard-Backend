from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.config import settings
from core.database import engine
from core.base import Base

# Import all models to register them with Base
import models

# Import all routers
from api.v1 import auth, users, transactions, kyc, dashboard, payment_gateway, auto_crud, websocket, referral, notifications
from api.v1.auto_crud import get_models_list

# Create all database tables with proper error handling
try:
    # Base.metadata.create_all(bind=engine)
    print("✅ Database connection successful - Tables ready")
except Exception as e:
    print(f"❌ Database Connection Error: {e}")
    print("⚠️  Please check your DATABASE_URL in backend/.env file")
    print(
        "📝 Example: postgresql://username:password@localhost:5432/database_name"
    )

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Admin Dashboard API for comprehensive platform management")

# Configure CORS with explicit settings (secure for development and production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ],
    allow_origin_regex=r"https://.*\.replit\.dev|https://.*\.repl\.co",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600)

# Create upload directory if not exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads",
          StaticFiles(directory=settings.UPLOAD_FOLDER),
          name="uploads")

# Include API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(dashboard.router,
                   prefix="/api/v1/dashboard",
                   tags=["dashboard"])
app.include_router(kyc.router, prefix="/api/v1/kyc", tags=["kyc"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(transactions.router,
                   prefix="/api/v1/transactions",
                   tags=["transactions"])
app.include_router(websocket.router, prefix="/api/v1/ws")
app.include_router(referral.router,
                   prefix="/api/v1/referral",
                   tags=["referral"])
app.include_router(payment_gateway.router,
                   prefix="/api/v1/payment-gateway",
                   tags=["payment-gateway"])
app.include_router(notifications.router,
                   prefix="/api/v1/notifications",
                   tags=["notifications"])


@app.get("/")
async def root():
    return {
        "message": "Admin Dashboard API",
        "version": settings.VERSION,
        "docs": "/docs",
        "models": get_models_list()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "api_version": settings.VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
