from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import os

from core.database import get_db
from core.config import settings
from core.auth import get_current_user, TokenData
from models.models import User, OfflineKYC, PanOfflineKYC

router = APIRouter(tags=["kyc"])

@router.get("/verification")
async def get_kyc_verification(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    kyc_status: Optional[str] = Query(None),
    limit: int = Query(500, le=1000),
    db: Session = Depends(get_db)
):
    """Get ALL users with KYC verification status filter"""
    try:
        from models.models import Aadhar_User, User_Aadhar_Address
        
        print(f"\n{'='*80}")
        print(f"🔍 KYC Verification API called")
        print(f"   Authenticated user: {current_user.username}")
        print(f"   kyc_status filter: {kyc_status}")
        print(f"   limit: {limit}")
        print(f"   Request URL: {request.url}")
        print(f"{'='*80}\n")
        
        # Get ALL users with left outer joins
        query = db.query(User, OfflineKYC, PanOfflineKYC, Aadhar_User, User_Aadhar_Address).outerjoin(
            OfflineKYC, User.UserID == OfflineKYC.user_id
        ).outerjoin(
            PanOfflineKYC, OfflineKYC.id == PanOfflineKYC.offline_kyc_id
        ).outerjoin(
            Aadhar_User, User.UserID == Aadhar_User.user_id
        ).outerjoin(
            User_Aadhar_Address, Aadhar_User.address_id == User_Aadhar_Address.id
        ).filter(User.IsDeleted == False)

        # Apply KYC status filter if provided
        if kyc_status and kyc_status.lower() not in ['all', 'none', '']:
            if kyc_status.lower() == 'verified':
                query = query.filter(
                    User.aadhar_verification_status == True,
                    User.pan_verification_status == True
                )
            elif kyc_status.lower() == 'partially verified':
                from sqlalchemy import or_, and_
                query = query.filter(
                    or_(
                        and_(User.aadhar_verification_status == True, User.pan_verification_status == False),
                        and_(User.aadhar_verification_status == False, User.pan_verification_status == True)
                    )
                )
            elif kyc_status.lower() == 'not verified':
                query = query.filter(
                    User.aadhar_verification_status == False,
                    User.pan_verification_status == False
                )

        results = query.order_by(desc(User.CreatedAt)).limit(limit).all()
        
        print(f"✅ Found {len(results)} KYC records")

        kyc_data = []
        for user, kyc, pan_data, aadhaar, address in results:
            # Determine KYC status based on verification
            aadhaar_verified = user.aadhar_verification_status or False
            pan_verified = user.pan_verification_status or False
            
            # Status logic: Verified (both), Partially Verified (one), Not Verified (none)
            if aadhaar_verified and pan_verified:
                kyc_status = 'Verified'
            elif aadhaar_verified or pan_verified:
                kyc_status = 'Partially Verified'
            else:
                kyc_status = 'Not Verified'

            # Build full image URLs with proper base URL (optimized)
            base_url = str(request.base_url).rstrip('/')

            # Optimized URL building without checking file existence
            aadhaar_front_url = f"{base_url}{settings.STATIC_URL_PATH}/{kyc.aadhar_front_filename}" if kyc and kyc.aadhar_front_filename else None
            aadhaar_back_url = f"{base_url}{settings.STATIC_URL_PATH}/{kyc.aadhar_back_filename}" if kyc and kyc.aadhar_back_filename else None
            pan_image_url = f"{base_url}{settings.STATIC_URL_PATH}/{pan_data.pan_front}" if pan_data and pan_data.pan_front else None

            kyc_record = {
                "id": f"KYC{user.UserID:06d}",
                "name": user.fullname or f"User {user.UserID}",
                "userId": str(user.UserID),
                "mobile": user.MobileNumber,
                "email": user.Email or "N/A",
                "documentType": "Aadhaar" if kyc else "N/A",
                "documentNumber": kyc.aadhar_no if kyc else (aadhaar.aadharNumber if aadhaar else "N/A"),
                "submittedOn": kyc.dob.strftime('%Y-%m-%d') if kyc and kyc.dob else user.CreatedAt.strftime('%Y-%m-%d') if user.CreatedAt else "",
                "submittedTime": user.CreatedAt.strftime('%H:%M:%S') if user.CreatedAt else "",
                "kycStatus": kyc_status,
                "verifiedBy": "Admin" if user.IsKYCCompleted else "",
                "aadhaarFront": f"/backend/uploads/{kyc.aadhar_front_filename}" if kyc and kyc.aadhar_front_filename else None,
                "aadhaarBack": f"/backend/uploads/{kyc.aadhar_back_filename}" if kyc and kyc.aadhar_back_filename else None,
                "panImage": f"/backend/uploads/{pan_data.pan_front}" if pan_data and pan_data.pan_front else None,
                "panNumber": pan_data.pan_no if pan_data else None,
                "panName": pan_data.pan_name if pan_data else None
            }
            
            # Add Aadhaar details from Aadhar_User table if available
            if aadhaar:
                kyc_record["aadhaarDetails"] = {
                    "name": aadhaar.name,
                    "aadharNumber": aadhaar.aadharNumber,
                    "maskedNumber": aadhaar.maskedNumber,
                    "dateOfBirth": aadhaar.dateOfBirth.strftime('%Y-%m-%d') if aadhaar.dateOfBirth else None,
                    "gender": aadhaar.gender,
                    "phone": aadhaar.phone,
                    "email": aadhaar.email,
                    "photo": aadhaar.photo
                }
                
                # Add address if available
                if address:
                    kyc_record["aadhaarDetails"]["address"] = {
                        "house": address.house,
                        "street": address.street,
                        "locality": address.locality,
                        "district": address.district,
                        "state": address.state,
                        "pin": address.pin,
                        "country": address.country or "India"
                    }
            
            kyc_data.append(kyc_record)

        print(f"\n{'='*80}")
        print(f"📊 Final Response Summary:")
        print(f"   Total records: {len(kyc_data)}")
        if len(kyc_data) > 0:
            print(f"   Sample record keys: {list(kyc_data[0].keys())}")
            print(f"   First record ID: {kyc_data[0]['id']}")
        print(f"{'='*80}\n")
        
        return kyc_data
    except Exception as e:
        print(f"❌ KYC API Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))