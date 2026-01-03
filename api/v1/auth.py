
from fastapi import APIRouter, HTTPException, status, Depends
from core.auth import (
    LoginRequest, LoginResponse, RefreshRequest,
    authenticate_user, create_access_token, create_refresh_token,
    verify_token, get_current_user, TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint - returns JWT access and refresh tokens"""
    try:
        print(f"🔐 Login attempt for user: {request.username}")
        
        if not authenticate_user(request.username, request.password):
            print(f"❌ Authentication failed for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create tokens
        token_data = {"username": request.username}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        print(f"✅ Login successful for user: {request.username}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            username=request.username,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh access token using refresh token"""
    token_data = verify_token(request.refresh_token, "refresh")
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new access token
    new_access_token = create_access_token({"username": token_data.username})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/verify")
async def verify_current_token(current_user: TokenData = Depends(get_current_user)):
    """Verify if current token is valid and return user info"""
    return {
        "valid": True,
        "username": current_user.username,
        "expires": current_user.exp.isoformat()
    }

@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """Logout endpoint - client should remove tokens"""
    return {
        "message": "Successfully logged out",
        "username": current_user.username
    }
