from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Dict, Any, List

from core.database import get_db
from core.auth import get_current_user, TokenData
from models.models import User

router = APIRouter(tags=["referral"])

def build_referral_tree(user: User, db: Session, current_level: int = 0, max_depth: int = 50) -> Dict[str, Any]:
    """Recursively build referral tree up to L50"""
    if current_level >= max_depth:
        return None

    # Get all users referred by this user (using introducer_id as sponsor)
    referred_users = db.query(User).filter(
        User.introducer_id == user.member_id,
        User.IsDeleted == False
    ).all()

    user_data = {
        "UserID": user.UserID,
        "fullname": user.fullname or f"User {user.UserID}",
        "member_id": user.member_id,
        "MobileNumber": user.MobileNumber,
        "Email": user.Email,
        "prime_status": user.prime_status,
        "referred_count": len(referred_users),
        "level": current_level,
        "sponsor_id": user.introducer_id,  # Who referred this user
        "depth_from_root": current_level,
        "referred_users": []
    }

    # Recursively build tree for referred users
    for ref_user in referred_users:
        child_tree = build_referral_tree(ref_user, db, current_level + 1, max_depth)
        if child_tree:
            user_data["referred_users"].append(child_tree)

    return user_data

@router.get("/matrix")
async def get_matrix_data(
    member_id: str = None,
    max_level: int = 50,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get matrix data for all users or a specific user's downline"""
    try:
        # If member_id is provided, get that user, otherwise get root users (users with no sponsor)
        if member_id:
            root_user = db.query(User).filter(
                User.member_id == member_id,
                User.IsDeleted == False
            ).first()

            if not root_user:
                raise HTTPException(status_code=404, detail="User not found")

            root_users = [root_user]
        else:
            # Get all root users (users with no introducer or self-sponsored)
            root_users = db.query(User).filter(
                User.IsDeleted == False,
                (User.introducer_id == None) | (User.introducer_id == User.member_id)
            ).limit(10).all()  # Limit to prevent too much data

        # Build matrix tree for each root user
        result = []
        for root in root_users:
            tree_data = build_matrix_tree(root, db, max_depth=max_level)
            result.append(tree_data)

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_matrix_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def build_matrix_tree(user: User, db: Session, current_level: int = 0, max_depth: int = 50) -> Dict[str, Any]:
    """Build matrix tree with level information (for Matrix Level page)"""
    if current_level >= max_depth:
        return None

    # Get all users referred by this user
    sponsored_users = db.query(User).filter(
        User.introducer_id == user.member_id,
        User.IsDeleted == False
    ).all()

    user_data = {
        "member_id": user.member_id,
        "fullname": user.fullname or f"User {user.UserID}",
        "mobile": user.MobileNumber,
        "level": current_level,
        "sponsored_count": len(sponsored_users),
        "sponsored_users": []
    }

    # Recursively build tree for sponsored users
    for sponsored in sponsored_users:
        child_tree = build_matrix_tree(sponsored, db, current_level + 1, max_depth)
        if child_tree:
            user_data["sponsored_users"].append(child_tree)

    return user_data

@router.get("/matrix/{member_id}")
async def get_matrix_data_for_user(
    member_id: str,
    max_level: int = 50,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get matrix data for a specific user"""
    try:
        user = db.query(User).filter(
            User.member_id == member_id,
            User.IsDeleted == False
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tree_data = build_matrix_tree(user, db, max_depth=max_level)
        return [tree_data] if tree_data else []

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_matrix_data_for_user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/referral-chain")
async def get_referral_chain(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete referral chain for a user"""
    try:
        user = db.query(User).filter(
            User.UserID == user_id,
            User.IsDeleted == False
        ).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build the referral tree
        referral_tree = build_referral_tree(user, db)

        # Calculate total referrals recursively
        def count_referrals(node: Dict) -> int:
            count = len(node.get("referred_users", []))
            for child in node.get("referred_users", []):
                count += count_referrals(child)
            return count

        # Calculate max depth
        def get_max_depth(node: Dict, current_depth: int = 0) -> int:
            if not node.get("referred_users"):
                return current_depth
            return max(get_max_depth(child, current_depth + 1) for child in node["referred_users"])

        total_referrals = count_referrals(referral_tree)
        max_depth = get_max_depth(referral_tree)

        return {
            "userName": user.fullname or f"User {user.UserID}",
            "totalReferrals": total_referrals,
            "maxDepth": max_depth,
            "chain": [referral_tree]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))