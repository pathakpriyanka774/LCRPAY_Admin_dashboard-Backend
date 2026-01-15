# from fastapi import APIRouter, Depends, Query, HTTPException
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import desc, or_, func
# from datetime import datetime
# from decimal import Decimal

# from core.database import get_db
# from core.auth import get_current_user, TokenData
# from models.payment_gateway import Payment_Gateway
# from models.models import User, LcrMoney, LcrRewards, BillTransactions
# from models.service_request import Service_Request

# router = APIRouter(tags=["transactions"])

# @router.get("/detail/{reference_id}")
# async def get_transaction_detail(
#     reference_id: str,
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get detailed transaction info including LCR money and rewards by reference_id"""
#     try:
#         print(f"🔍 Searching for reference_id: {reference_id}")

#         # Find service request by reference_id
#         service_req = db.query(Service_Request).filter(
#             Service_Request.reference_id == reference_id
#         ).first()

#         if not service_req:
#             print(f"⚠️ No service request found for reference_id: {reference_id}")
#             return {
#                 "reference_id": reference_id,
#                 "service_type": "N/A",
#                 "amount": 0,
#                 "lcr_money": 0,
#                 "lcr_reward": 0,
#                 "money_status": "Not Found",
#                 "reward_status": "Not Found",
#                 "status": "Not Found",
#                 "prime_activation": None
#             }

#         print(f"✅ Found service request: ID={service_req.id}, Status={service_req.status}")

#         # Get LCR Money total for this reference_id
#         lcr_money_total = db.query(func.sum(LcrMoney.amount)).filter(
#             LcrMoney.reference_id == reference_id
#         ).scalar() or Decimal('0.00')

#         # Get LCR Rewards total for this reference_id
#         lcr_reward_total = db.query(func.sum(LcrRewards.amount)).filter(
#             LcrRewards.reference_id == reference_id
#         ).scalar() or Decimal('0.00')

#         print(f"💰 LCR Money Total: {lcr_money_total}, LCR Reward Total: {lcr_reward_total}")

#         # Check if this is a Prime Activation transaction
#         prime_activation = None
#         if service_req.service_type and 'prime' in service_req.service_type.lower():
#             from models.models import PrimeActivations, User

#             print(f"🔍 Checking for Prime Activation with reference_id: {reference_id}")

#             prime_record = db.query(PrimeActivations).options(
#                 joinedload(PrimeActivations.receiver_member),
#                 joinedload(PrimeActivations.prime_activator)
#             ).filter(
#                 PrimeActivations.reference_id == reference_id
#             ).first()

#             if prime_record:
#                 print(f"✅ Found Prime Activation: member={prime_record.member}, paid_by={prime_record.prime_initiated_by}")

#                 # Use relationships instead of separate queries
#                 activated_user = prime_record.receiver_member
#                 initiator_user = prime_record.prime_activator

#                 prime_activation = {
#                     "activated_member_id": prime_record.member,
#                     "activated_member_name": activated_user.fullname if activated_user else "Unknown",
#                     "activated_member_mobile": activated_user.MobileNumber if activated_user else "N/A",
#                     "paid_by_member_id": prime_record.prime_initiated_by,
#                     "paid_by_name": initiator_user.fullname if initiator_user else "Unknown",
#                     "paid_by_mobile": initiator_user.MobileNumber if initiator_user else "N/A",
#                     "package_amount": float(prime_record.package_amount) if prime_record.package_amount else 0,
#                     "activation_date": prime_record.activation_date.isoformat() if prime_record.activation_date else None
#                 }

#                 print(f"📦 Prime Activation Details: {prime_activation}")
#             else:
#                 print(f"⚠️ No Prime Activation found for reference_id: {reference_id}")

#         # Determine status based on service request status
#         is_completed = service_req.status.lower() in ['completed', 'paid', 'success']

#         return {
#             "reference_id": reference_id,
#             "service_type": service_req.service_type or "N/A",
#             "amount": float(service_req.amount) if service_req.amount else 0,
#             "lcr_money": float(lcr_money_total),
#             "lcr_reward": float(lcr_reward_total),
#             "money_status": "Credited" if is_completed else "Pending",
#             "reward_status": "Credited" if is_completed else "Pending",
#             "status": service_req.status,
#             "prime_activation": prime_activation
#         }

#     except Exception as e:
#         print(f"❌ Error in get_transaction_detail: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# @router.get("/service-types")
# async def get_service_types(
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all unique service types"""
#     try:
#         service_types = db.query(Service_Request.service_type).distinct().all()
#         return [st[0] for st in service_types if st[0]]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/mobile")
# async def get_mobile_transactions(
#     current_user: TokenData = Depends(get_current_user),
#     limit: int = Query(500, le=1000),
#     service_type: str = Query(None),
#     status: str = Query(None),
#     page: int = Query(1, ge=1),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get mobile recharge transactions only (excluding Prime, BBPS, DTH)
#     Professional query with proper filtering logic
#     """
#     try:
#         # Base query - ONLY mobile recharge services (strict filtering) - including pending status
#         query = db.query(Service_Request).filter(
#             Service_Request.status.in_(['completed', 'failed', 'processing', 'paid', 'pending']),
#             Service_Request.service_type.ilike('%mobile%'),
#             Service_Request.service_type.ilike('%recharge%'),
#             ~Service_Request.service_type.ilike('%prime%'),
#             ~Service_Request.service_type.ilike('%dth%'),
#             ~Service_Request.service_type.ilike('%bbps%'),
#             ~Service_Request.service_type.ilike('%bill%')
#         )

#         # Apply service type filter if provided
#         if service_type and service_type != 'all':
#             query = query.filter(Service_Request.service_type == service_type)

#         # Apply status filter if provided
#         if status and status != 'all':
#             query = query.filter(Service_Request.status == status)

#         offset = (page - 1) * limit
#         service_requests = query.order_by(desc(Service_Request.created_at)).limit(limit).offset(offset).all()

#         # Get user IDs for batch lookup
#         user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))

#         # Batch fetch user names
#         users_dict = {}
#         if user_ids:
#             users = db.query(User.UserID, User.fullname, User.member_id).filter(
#                 User.UserID.in_(user_ids)
#             ).all()
#             users_dict = {u.UserID: {"name": u.fullname or f"User {u.UserID}", "member_id": u.member_id} for u in users}

#         result = []
#         for sr in service_requests:
#             user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A"})

#             result.append({
#                 "id": sr.id,
#                 "user_id": sr.user_id,
#                 "user_name": user_info["name"],
#                 "user_member_id": user_info["member_id"],
#                 "service_type": sr.service_type or "N/A",
#                 "operator_code": sr.operator_code,
#                 "mobile_number": sr.mobile_number,
#                 "amount": str(sr.amount) if sr.amount else "0",
#                 "reference_id": sr.reference_id or "N/A",
#                 "status": sr.status or "unknown",
#                 "payment_txn_id": sr.payment_txn_id,
#                 "utr_no": sr.utr_no,
#                 "created_at": sr.created_at.isoformat() if sr.created_at else None,
#                 "updated_at": sr.updated_at.isoformat() if sr.updated_at else None
#             })

#         # Fetch total count for pagination metadata
#         total_records = query.count()

#         return {
#             "transactions": result,
#             "pagination": {
#                 "current_page": page,
#                 "page_size": limit,
#                 "total_records": total_records,
#                 "total_pages": (total_records + limit - 1) // limit
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/payment-details/{reference_id}")
# async def get_payment_details(
#     reference_id: str,
#     current_user: TokenData = Depends(get_current_user),
#     lcr_money_page: int = Query(1, ge=1),
#     lcr_rewards_page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=10, le=50),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get complete payment details for a reference ID
#     Uses reference_id to JOIN service_request, lcrmoney, and lcr_rewards tables
#     Professional implementation with optimized queries
#     """
#     try:
#         # Primary query - get service request by reference_id
#         service_request = (
#             db.query(Service_Request)
#             .filter(Service_Request.reference_id == reference_id)
#             .first()
#         )

#         if not service_request:
#             raise HTTPException(status_code=404, detail=f"Service request not found for reference_id: {reference_id}")

#         # Get user details - optimized single query
#         user = db.query(
#             User.UserID, User.fullname, User.MobileNumber, User.Email, User.member_id
#         ).filter(User.UserID == service_request.user_id).first()

#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Payment Gateway transactions - related to this service request
#         payments = db.query(Payment_Gateway).filter(
#             Payment_Gateway.service_request_id == service_request.id
#         ).order_by(desc(Payment_Gateway.created_at)).limit(10).all()

#         # LCR Money - JOIN by reference_id (PRIMARY) + user_id fallback
#         lcr_money_offset = (lcr_money_page - 1) * page_size
#         lcr_money_query = db.query(LcrMoney).filter(
#             LcrMoney.reference_id == reference_id
#         )

#         lcr_money = lcr_money_query.order_by(
#             desc(LcrMoney.transactiondate)
#         ).limit(page_size).offset(lcr_money_offset).all()

#         lcr_money_total = lcr_money_query.count()

#         # Calculate total distributed LCRmoney
#         lcr_money_total_amount = db.query(func.sum(LcrMoney.amount)).filter(
#             LcrMoney.reference_id == reference_id
#         ).scalar() or Decimal('0.00000')

#         # LCR Rewards - JOIN by reference_id (PRIMARY) + user_id fallback
#         lcr_rewards_offset = (lcr_rewards_page - 1) * page_size
#         lcr_rewards_query = db.query(LcrRewards).filter(
#             LcrRewards.reference_id == reference_id
#         )

#         lcr_rewards = lcr_rewards_query.order_by(
#             desc(LcrRewards.transactiondate)
#         ).limit(page_size).offset(lcr_rewards_offset).all()

#         lcr_rewards_total = lcr_rewards_query.count()

#         # Calculate total distributed LCR_rewards
#         lcr_rewards_total_amount = db.query(func.sum(LcrRewards.amount)).filter(
#             LcrRewards.reference_id == reference_id
#         ).scalar() or Decimal('0.00000')

#         return {
#             "service_request": {
#                 "id": service_request.id,
#                 "reference_id": service_request.reference_id,
#                 "service_type": service_request.service_type,
#                 "operator_code": service_request.operator_code,
#                 "mobile_number": service_request.mobile_number,
#                 "amount": float(service_request.amount),
#                 "status": service_request.status,
#                 "payment_txn_id": service_request.payment_txn_id,
#                 "utr_no": service_request.utr_no,
#                 "created_at": service_request.created_at.isoformat() if service_request.created_at else None,
#                 "updated_at": service_request.updated_at.isoformat() if service_request.updated_at else None,
#                 "metadata": service_request.service_metadata
#             },
#             "user": {
#                 "id": user.UserID if user else None,
#                 "name": user.fullname if user else "Unknown",
#                 "mobile": user.MobileNumber if user else "N/A",
#                 "email": user.Email if user else "N/A",
#                 "member_id": user.member_id if user else "N/A"
#             },
#             "payment_gateway_transactions": [
#                 {
#                     "id": pg.id,
#                     "client_txn_id": pg.client_txn_id,
#                     "sabpaisa_txn_id": pg.sabpaisa_txn_id,
#                     "payer_name": pg.payer_name,
#                     "payer_email": pg.payer_email,
#                     "payer_mobile": pg.payer_mobile,
#                     "amount": float(pg.amount) if pg.amount else 0,
#                     "paid_amount": float(pg.paid_amount) if pg.paid_amount else 0,
#                     "payment_mode": pg.payment_mode,
#                     "bank_name": pg.bank_name,
#                     "rrn": pg.rrn,
#                     "purpose": pg.purpose,
#                     "status": pg.status,
#                     "status_code": pg.status_code,
#                     "sabpaisa_message": pg.sabpaisa_message,
#                     "service_data": pg.service_data,
#                     "amount_type": pg.amount_type,
#                     "challan_number": pg.challan_number,
#                     "bank_error_code": pg.bank_error_code,
#                     "sabpaisa_error_code": pg.sabpaisa_error_code,
#                     "trans_date": pg.trans_date.isoformat() if pg.trans_date else None,
#                     "created_at": pg.created_at.isoformat() if pg.created_at else None,
#                     "updated_at": pg.updated_at.isoformat() if pg.updated_at else None
#                 }
#                 for pg in payments
#             ],
#             "lcr_money_transactions": [
#                 {
#                     "id": lm.srno,
#                     "amount": float(lm.amount) if lm.amount else 0.0,
#                     "type": lm.transactiontype or "N/A",
#                     "received_by": lm.received_by or "N/A",
#                     "received_from": lm.received_from or "N/A",
#                     "status": "Active" if lm.status == 1 else "Inactive",
#                     "date": lm.transactiondate.strftime('%Y-%m-%d') if lm.transactiondate else "N/A",
#                     "time": lm.transactiondate.strftime('%H:%M:%S') if lm.transactiondate else "N/A",
#                     "purpose": lm.purpose or "N/A",
#                     "remark": lm.remark or "N/A"
#                 }
#                 for lm in lcr_money
#             ],
#             "lcr_rewards_transactions": [
#                 {
#                     "id": lr.srno,
#                     "amount": float(lr.amount) if lr.amount else 0.0,
#                     "type": lr.transactiontype or "N/A",
#                     "received_by": lr.received_by or "N/A",
#                     "received_from": lr.received_from or "N/A",
#                     "status": "Active" if lr.status == 1 else "Inactive",
#                     "date": lr.transactiondate.strftime('%Y-%m-%d') if lr.transactiondate else "N/A",
#                     "time": lr.transactiondate.strftime('%H:%M:%S') if lr.transactiondate else "N/A",
#                     "purpose": lr.purpose or "N/A",
#                     "remark": lr.remark or "N/A"
#                 }
#                 for lr in lcr_rewards
#             ],
#             "pagination": {
#                 "lcr_money": {
#                     "current_page": lcr_money_page,
#                     "page_size": page_size,
#                     "total_records": lcr_money_total,
#                     "total_pages": (lcr_money_total + page_size - 1) // page_size
#                 },
#                 "lcr_rewards": {
#                     "current_page": lcr_rewards_page,
#                     "page_size": page_size,
#                     "total_records": lcr_rewards_total,
#                     "total_pages": (lcr_rewards_total + page_size - 1) // page_size
#                 }
#             },
#             "totals": {
#                 "lcr_money_distributed": float(lcr_money_total_amount),
#                 "lcr_rewards_distributed": float(lcr_rewards_total_amount)
#             }
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/dth")
# async def get_dth_transactions(
#     current_user: TokenData = Depends(get_current_user),
#     limit: int = Query(100, le=500),
#     page: int = Query(1, ge=1),
#     db: Session = Depends(get_db)
# ):
#     """Get DTH recharge transactions"""
#     try:
#         query = db.query(Payment_Gateway).join(
#             User, Payment_Gateway.payer_mobile == User.MobileNumber
#         ).filter(
#             Payment_Gateway.purpose.ilike('%dth%')
#         )

#         offset = (page - 1) * limit
#         transactions = query.order_by(desc(Payment_Gateway.created_at)).limit(limit).offset(offset).all()

#         result = []
#         for txn in transactions:
#             user = db.query(User).filter(User.MobileNumber == txn.payer_mobile).first()
#             result.append({
#                 "id": txn.id,
#                 "transactionId": f"DTH{txn.id:06d}",
#                 "user": txn.payer_name or (user.fullname if user else "Unknown"),
#                 "subscriberId": txn.service_data.get('subscriber_id', f"SUB{txn.id}") if txn.service_data else f"SUB{txn.id}",
#                 "operator": txn.service_data.get('operator', 'Unknown') if txn.service_data else 'Unknown',
#                 "plan": txn.service_data.get('plan', 'Standard') if txn.service_data else 'Standard',
#                 "amount": float(txn.amount) if txn.amount else 0,
#                 "status": "Success" if txn.status == "success" else "Pending" if txn.status == "pending" else "Failed",
#                 "date": txn.created_at.strftime('%Y-%m-%d') if txn.created_at else "",
#                 "time": txn.created_at.strftime('%H:%M:%S') if txn.created_at else "",
#                 "referenceId": txn.rrn or f"REF{txn.id}"
#             })

#         total_records = query.count()

#         return {
#             "transactions": result,
#             "pagination": {
#                 "current_page": page,
#                 "page_size": limit,
#                 "total_records": total_records,
#                 "total_pages": (total_records + limit - 1) // limit
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/other")
# async def get_other_transactions(
#     current_user: TokenData = Depends(get_current_user),
#     limit: int = Query(500, le=1000),
#     service_type: str = Query(None),
#     status: str = Query(None),
#     page: int = Query(1, ge=1),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get other service transactions (Prime Activation, BBPS, etc.)
#     Excludes Mobile Recharge and DTH - Professional implementation
#     """
#     try:
#         # Base query - Prime Activation, BBPS and other services - including pending status
#         # EXCLUDE mobile recharge and DTH completely
#         query = db.query(Service_Request).filter(
#             Service_Request.status.in_(['completed', 'failed', 'processing', 'paid', 'pending']),
#             or_(
#                 Service_Request.service_type.ilike('%prime%'),
#                 Service_Request.service_type.ilike('%bbps%'),
#                 Service_Request.service_type.ilike('%bill%')
#             ),
#             ~Service_Request.service_type.ilike('%mobile%'),
#             ~Service_Request.service_type.ilike('%dth%')
#         )

#         # Apply service type filter if provided
#         if service_type and service_type != 'all':
#             query = query.filter(Service_Request.service_type == service_type)

#         # Apply status filter if provided
#         if status and status != 'all':
#             query = query.filter(Service_Request.status == status)

#         offset = (page - 1) * limit
#         service_requests = query.order_by(desc(Service_Request.created_at)).limit(limit).offset(offset).all()

#         # Get user IDs for batch lookup
#         user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))

#         # Batch fetch user names
#         users_dict = {}
#         if user_ids:
#             users = db.query(User.UserID, User.fullname, User.member_id).filter(
#                 User.UserID.in_(user_ids)
#             ).all()
#             users_dict = {u.UserID: {"name": u.fullname or f"User {u.UserID}", "member_id": u.member_id} for u in users}

#         result = []
#         for sr in service_requests:
#             user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A"})

#             result.append({
#                 "id": sr.id,
#                 "user_id": sr.user_id,
#                 "user_name": user_info["name"],
#                 "user_member_id": user_info["member_id"],
#                 "service_type": sr.service_type or "Other Service",
#                 "operator_code": sr.operator_code,
#                 "mobile_number": sr.mobile_number,
#                 "amount": str(sr.amount) if sr.amount else "0",
#                 "reference_id": sr.reference_id or "N/A",
#                 "status": sr.status or "unknown",
#                 "payment_txn_id": sr.payment_txn_id,
#                 "utr_no": sr.utr_no,
#                 "created_at": sr.created_at.isoformat() if sr.created_at else None,
#                 "updated_at": sr.updated_at.isoformat() if sr.updated_at else None
#             })

#         total_records = query.count()

#         return {
#             "transactions": result,
#             "pagination": {
#                 "current_page": page,
#                 "page_size": limit,
#                 "total_records": total_records,
#                 "total_pages": (total_records + limit - 1) // limit
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/user/{user_id}/all")
# async def get_user_all_transactions(
#     user_id: int,
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all transactions for a specific user - Service Requests + LCR Money + LCR Rewards (joined by reference_id)"""
#     try:
#         # Get user details
#         user = db.query(User).filter(User.UserID == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         # Service Requests (excluding pending)
#         service_requests = db.query(Service_Request).filter(
#             Service_Request.user_id == user_id,
#             Service_Request.status != 'pending'
#         ).order_by(desc(Service_Request.created_at)).all()

#         # Get all reference_ids for joining
#         service_reference_ids = [sr.reference_id for sr in service_requests if sr.reference_id]

#         # Get all mobile numbers from service requests to look up recipient users
#         mobile_numbers = [sr.mobile_number for sr in service_requests if sr.mobile_number]

#         # Batch lookup: Find users by mobile numbers (who was recharged)
#         recipient_users = {}
#         if mobile_numbers:
#             recipients = db.query(User).filter(User.MobileNumber.in_(mobile_numbers)).all()
#             recipient_users = {u.MobileNumber: u for u in recipients}

#         # Batch lookup: Find prime activation details by reference_id
#         from models.models import PrimeActivations
#         prime_activations = {}
#         prime_member_ids = set()
#         if service_reference_ids:
#             primes = db.query(PrimeActivations).filter(
#                 PrimeActivations.reference_id.in_(service_reference_ids)
#             ).all()
#             prime_activations = {p.reference_id: p for p in primes}
#             prime_member_ids = {p.member for p in primes if p.member}

#         # Batch lookup: Find users by member IDs for prime activations
#         prime_recipients = {}
#         if prime_member_ids:
#             prime_users = db.query(User).filter(User.member_id.in_(prime_member_ids)).all()
#             prime_recipients = {u.member_id: u for u in prime_users}

#         # LCR Bones - joined by reference_id
#         lcr_bones = []
#         if service_reference_ids:
#             lcr_bones = db.query(LcrMoney).filter(
#                 LcrMoney.reference_id.in_(service_reference_ids)
#             ).order_by(desc(LcrMoney.transactiondate)).all()

#         # LCR Rewards - joined by reference_id
#         lcr_rewards = []
#         if service_reference_ids:
#             lcr_rewards = db.query(LcrRewards).filter(
#                 LcrRewards.reference_id.in_(service_reference_ids)
#             ).order_by(desc(LcrRewards.transactiondate)).all()

#         # Build service requests with recipient info
#         service_requests_data = []
#         for sr in service_requests:
#             recipient_info = None

#             # Check if this is a prime activation (check first as it's more specific)
#             if sr.reference_id and sr.reference_id in prime_activations:
#                 prime = prime_activations[sr.reference_id]
#                 # Get the member who received prime from pre-loaded dict
#                 if prime.member and prime.member in prime_recipients:
#                     prime_recipient = prime_recipients[prime.member]
#                     recipient_info = {
#                         "type": "prime_activation",
#                         "user_id": prime_recipient.UserID,
#                         "name": prime_recipient.fullname or f"User {prime_recipient.UserID}",
#                         "member_id": prime_recipient.member_id,
#                         "mobile": prime_recipient.MobileNumber
#                     }

#             # Check if this is a mobile recharge to another user (not self)
#             elif sr.mobile_number and sr.mobile_number != user.MobileNumber and sr.mobile_number in recipient_users:
#                 recipient = recipient_users[sr.mobile_number]
#                 recipient_info = {
#                     "type": "mobile_recharge",
#                     "user_id": recipient.UserID,
#                     "name": recipient.fullname or f"User {recipient.UserID}",
#                     "member_id": recipient.member_id,
#                     "mobile": recipient.MobileNumber
#                 }

#             # Check if user recharged their own number
#             elif sr.mobile_number and sr.mobile_number == user.MobileNumber:
#                 recipient_info = {
#                     "type": "mobile_recharge",
#                     "user_id": user.UserID,
#                     "name": user.fullname or f"User {user.UserID}",
#                     "member_id": user.member_id,
#                     "mobile": user.MobileNumber
#                 }

#             # If mobile number but no user found, show as external
#             elif sr.mobile_number:
#                 recipient_info = {
#                     "type": "external_mobile",
#                     "mobile": sr.mobile_number,
#                     "name": "External User"
#                 }

#             service_requests_data.append({
#                 "id": sr.id,
#                 "reference_id": sr.reference_id,
#                 "service_type": sr.service_type,
#                 "operator": sr.operator_code or "N/A",
#                 "mobile": sr.mobile_number or "N/A",
#                 "amount": float(sr.amount),
#                 "status": sr.status.capitalize(),
#                 "payment_txn_id": sr.payment_txn_id or "N/A",
#                 "utr_no": sr.utr_no or "N/A",
#                 "date": sr.created_at.strftime('%Y-%m-%d'),
#                 "time": sr.created_at.strftime('%H:%M:%S'),
#                 "recipient": recipient_info  # NEW: Who was recharged or whose prime was activated
#             })

#         return {
#             "user": {
#                 "id": user.UserID,
#                 "name": user.fullname,
#                 "member_id": user.member_id,
#                 "mobile": user.MobileNumber
#             },
#             "service_requests": service_requests_data,
#             "lcr_bones": [
#                 {
#                     "id": lb.srno,
#                     "reference_id": lb.reference_id or "N/A",
#                     "amount": float(lb.amount) if lb.amount else 0.0,
#                     "type": lb.transactiontype or "N/A",
#                     "received_by": lb.received_by or "N/A",
#                     "received_from": lb.received_from or "N/A",
#                     "status": "Active" if lb.status == 1 else "Inactive",
#                     "date": lb.transactiondate.strftime('%Y-%m-%d') if lb.transactiondate else "N/A",
#                     "time": lb.transactiondate.strftime('%H:%M:%S') if lb.transactiondate else "N/A",
#                     "purpose": lb.purpose or "N/A",
#                     "remark": lb.remark or "N/A"
#                 }
#                 for lb in lcr_bones
#             ],
#             "lcr_rewards": [
#                 {
#                     "id": lr.srno,
#                     "reference_id": lr.reference_id or "N/A",
#                     "amount": float(lr.amount) if lr.amount else 0.0,
#                     "type": lr.transactiontype or "N/A",
#                     "received_by": lr.received_by or "N/A",
#                     "received_from": lr.received_from or "N/A",
#                     "status": "Active" if lr.status == 1 else "Inactive",
#                     "date": lr.transactiondate.strftime('%Y-%m-%d') if lr.transactiondate else "N/A",
#                     "time": lr.transactiondate.strftime('%H:%M:%S') if lr.transactiondate else "N/A",
#                     "purpose": lr.purpose or "N/A",
#                     "remark": lr.remark or "N/A"
#                 }
#                 for lr in lcr_rewards
#             ]
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # Placeholder for Matrix Level Menu and its related logic
# @router.get("/matrix-levels")
# async def get_matrix_levels(
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     This endpoint will provide data for the Matrix Level Menu.
#     It will group users into levels (L1-L10, L11-L20, etc.)
#     and display their status.
#     Pagination will be applied for large datasets.
#     """
#     # TODO: Implement logic to query users, determine their level, and return paginated results.
#     # This will involve complex SQL queries or data processing.
#     # Example: Fetch all users, then process them to determine their level based on criteria.
#     # For now, returning a placeholder response.
#     raise HTTPException(status_code=501, detail="Matrix Level functionality not yet implemented.")


# @router.get("/all-records")
# async def get_all_records(
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(100, le=500),
#     status: str = Query(None),
#     service_type: str = Query(None)
# ):
#     """
#     Fetches ALL records from Service_Request with ALL statuses
#     Optimized for performance with proper pagination
#     Supports filtering by status and service_type
#     Shows who paid to whom for each transaction
#     """
#     try:
#         print(f"📊 [API] /all-records called - Filters: status={status}, service_type={service_type}, page={page}, page_size={page_size}")
        
#         # Base query - Include ALL statuses with optimized loading
#         query = db.query(Service_Request)

#         # Apply status filter (exact match for better filtering)
#         if status and status.lower() not in ['all', 'none', '']:
#             query = query.filter(Service_Request.status == status.lower())
#             print(f"✅ Status filter applied: {status.lower()}")

#         # Apply service type filter
#         if service_type and service_type.lower() not in ['all', 'none', '']:
#             if service_type.lower() == 'mobile recharge':
#                 query = query.filter(
#                     Service_Request.service_type.ilike('%mobile%'),
#                     Service_Request.service_type.ilike('%recharge%'),
#                     ~Service_Request.service_type.ilike('%prime%')
#                 )
#             elif service_type.lower() == 'prime activation':
#                 query = query.filter(Service_Request.service_type.ilike('%prime%'))
#             elif service_type.lower() in ['dth recharge', 'd2h recharge', 'dth services']:
#                 query = query.filter(
#                     or_(
#                         Service_Request.service_type.ilike('%dth%'),
#                         Service_Request.service_type.ilike('%d2h%')
#                     )
#                 )
#             elif service_type.lower() == 'others':
#                 query = query.filter(
#                     ~Service_Request.service_type.ilike('%mobile%'),
#                     ~Service_Request.service_type.ilike('%prime%'),
#                     ~Service_Request.service_type.ilike('%dth%'),
#                     ~Service_Request.service_type.ilike('%d2h%'),
#                     ~Service_Request.service_type.ilike('%recharge%')
#                 )
#             print(f"✅ Service type filter applied: {service_type}")

#         # Get total count before pagination
#         total_records = query.count()
#         print(f"📊 Total records matching filters: {total_records}")

#         # Apply pagination
#         offset = (page - 1) * page_size
#         service_requests = query.order_by(desc(Service_Request.created_at)).limit(page_size).offset(offset).all()

#         # Get user IDs for batch lookup
#         user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))

#         # Batch fetch user details (who initiated the transaction)
#         users_dict = {}
#         if user_ids:
#             users = db.query(User.UserID, User.fullname, User.member_id, User.MobileNumber).filter(
#                 User.UserID.in_(user_ids)
#             ).all()
#             users_dict = {u.UserID: {"name": u.fullname or f"User {u.UserID}", "member_id": u.member_id, "mobile": u.MobileNumber} for u in users}

#         # Get prime activation details
#         from models.models import PrimeActivations
#         reference_ids = [sr.reference_id for sr in service_requests if sr.reference_id]
#         prime_activations = {}
#         prime_member_ids = set()
        
#         if reference_ids:
#             primes = db.query(PrimeActivations).options(
#                 joinedload(PrimeActivations.receiver_member),
#                 joinedload(PrimeActivations.prime_activator)
#             ).filter(PrimeActivations.reference_id.in_(reference_ids)).all()
#             prime_activations = {p.reference_id: p for p in primes}
#             print(f"✅ Found {len(prime_activations)} prime activations")

#         # Get recipient users by mobile number (for mobile recharge)
#         mobile_numbers = [sr.mobile_number for sr in service_requests if sr.mobile_number]
#         recipient_users = {}
#         if mobile_numbers:
#             recipients = db.query(User).filter(User.MobileNumber.in_(mobile_numbers)).all()
#             recipient_users = {u.MobileNumber: u for u in recipients}

#         result = []
#         for sr in service_requests:
#             user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A", "mobile": "N/A"})

#             # Determine payment_by and payment_for
#             payment_by = {
#                 "name": user_info["name"],
#                 "member_id": user_info["member_id"],
#                 "mobile": user_info["mobile"]
#             }
            
#             payment_for = None
#             prime_data = None

#             # Check for Prime Activation (highest priority)
#             if sr.reference_id in prime_activations:
#                 prime = prime_activations[sr.reference_id]
#                 activated_user = prime.receiver_member
#                 initiator_user = prime.prime_activator
                
#                 # Payment BY is the initiator
#                 payment_by = {
#                     "name": initiator_user.fullname if initiator_user else "Unknown",
#                     "member_id": prime.prime_initiated_by,
#                     "mobile": initiator_user.MobileNumber if initiator_user else "N/A"
#                 }
                
#                 # Payment FOR is the receiver
#                 payment_for = {
#                     "name": activated_user.fullname if activated_user else "Unknown",
#                     "member_id": prime.member,
#                     "mobile": activated_user.MobileNumber if activated_user else "N/A",
#                     "type": "Prime Activation"
#                 }
                
#                 prime_data = {
#                     "activated_member_id": prime.member,
#                     "activated_member_name": activated_user.fullname if activated_user else "Unknown",
#                     "activated_member_mobile": activated_user.MobileNumber if activated_user else "N/A",
#                     "paid_by_member_id": prime.prime_initiated_by,
#                     "paid_by_name": initiator_user.fullname if initiator_user else "Unknown",
#                     "paid_by_mobile": initiator_user.MobileNumber if initiator_user else "N/A",
#                     "package_amount": float(prime.package_amount) if prime.package_amount else 0,
#                     "activation_date": prime.activation_date.isoformat() if prime.activation_date else None
#                 }
            
#             # Check for Mobile/DTH Recharge
#             elif sr.mobile_number:
#                 # Check if recipient is a registered user
#                 if sr.mobile_number in recipient_users:
#                     recipient = recipient_users[sr.mobile_number]
#                     payment_for = {
#                         "name": recipient.fullname or "Unknown",
#                         "member_id": recipient.member_id,
#                         "mobile": sr.mobile_number,
#                         "type": "Mobile/DTH Recharge"
#                     }
#                 else:
#                     # External number (not a registered user)
#                     payment_for = {
#                         "name": "External User",
#                         "member_id": "N/A",
#                         "mobile": sr.mobile_number,
#                         "type": "Mobile/DTH Recharge"
#                     }

#             result.append({
#                 "id": sr.id,
#                 "user_id": sr.user_id,
#                 "user_name": user_info["name"],
#                 "user_member_id": user_info["member_id"],
#                 "user_mobile": user_info["mobile"],
#                 "service_type": sr.service_type or "N/A",
#                 "operator_code": sr.operator_code,
#                 "mobile_number": sr.mobile_number,
#                 "amount": str(sr.amount) if sr.amount else "0",
#                 "reference_id": sr.reference_id or "N/A",
#                 "status": sr.status or "unknown",
#                 "payment_txn_id": sr.payment_txn_id,
#                 "utr_no": sr.utr_no,
#                 "created_at": sr.created_at.isoformat() if sr.created_at else None,
#                 "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
#                 "payment_by": payment_by,  # Who paid
#                 "payment_for": payment_for,  # Who received the service
#                 "prime_activation": prime_data
#             })

#         print(f"✅ Returning {len(result)} records")

#         return {
#             "transactions": result,
#             "pagination": {
#                 "current_page": page,
#                 "page_size": page_size,
#                 "total_records": total_records,
#                 "total_pages": (total_records + page_size - 1) // page_size
#             }
#         }

#     except Exception as e:
#         print(f"❌ Error in get_all_records: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/history/{reference_id}")
# async def get_transaction_history(
#     reference_id: str,
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Get complete transaction history for a reference_id
#     Returns Service_Request + LCR Money + LCR Rewards linked by reference_id
#     """
#     try:
#         print(f"📊 [API] /history/{reference_id} called")
        
#         # Fetch LCR Money transactions
#         lcr_money_records = db.query(LcrMoney).filter(
#             LcrMoney.reference_id == reference_id
#         ).all()
        
#         # Fetch LCR Rewards transactions
#         lcr_rewards_records = db.query(LcrRewards).filter(
#             LcrRewards.reference_id == reference_id
#         ).all()
        
#         # Format LCR Money
#         lcr_money_data = []
#         for lm in lcr_money_records:
#             lcr_money_data.append({
#                 "srno": lm.srno,
#                 "amount": float(lm.amount) if lm.amount else 0.0,
#                 "transaction_type": lm.transactiontype or "N/A",
#                 "received_by": lm.received_by or "N/A",
#                 "received_from": lm.received_from or "N/A",
#                 "received_for": lm.received_for or "N/A",
#                 "purpose": lm.purpose or "N/A",
#                 "remark": lm.remark or "N/A",
#                 "transaction_date": lm.transactiondate.isoformat() if lm.transactiondate else None,
#                 "status": lm.status,
#                 "validity": lm.validity.isoformat() if lm.validity else None
#             })
        
#         # Format LCR Rewards
#         lcr_rewards_data = []
#         for lr in lcr_rewards_records:
#             lcr_rewards_data.append({
#                 "srno": lr.srno,
#                 "amount": float(lr.amount) if lr.amount else 0.0,
#                 "transaction_type": lr.transactiontype or "N/A",
#                 "received_by": lr.received_by or "N/A",
#                 "received_from": lr.received_from or "N/A",
#                 "received_for": lr.received_for or "N/A",
#                 "purpose": lr.purpose or "N/A",
#                 "remark": lr.remark or "N/A",
#                 "transaction_date": lr.transactiondate.isoformat() if lr.transactiondate else None,
#                 "status": lr.status,
#                 "validity": lr.validity.isoformat() if lr.validity else None
#             })
        
#         print(f"✅ Found {len(lcr_money_data)} LCR Money records and {len(lcr_rewards_data)} LCR Rewards records")
        
#         return {
#             "reference_id": reference_id,
#             "lcr_money": lcr_money_data,
#             "lcr_rewards": lcr_rewards_data
#         }
        
#     except Exception as e:
#         print(f"❌ Error in get_transaction_history: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/bill-transactions")
# async def get_bill_transactions(
#     current_user: TokenData = Depends(get_current_user),
#     db: Session = Depends(get_db),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(100, le=500),
#     payment_status: str = Query(None),
#     service_category: str = Query(None)
# ):
#     """
#     Get all transactions from Service_Request table with payment details
#     Filters: payment_status (completed, failed, pending, processing, all)
#              service_category (Mobile Recharge, Prime Activation, DTH, Others, All)
#     Shows: Payment By and Payment For information
#     """
#     try:
#         print(f"📊 [API] /bill-transactions called - page={page}, page_size={page_size}, payment_status={payment_status}, service_category={service_category}")
        
#         # Base query from Service_Request table
#         query = db.query(Service_Request)
        
#         # Apply payment status filter
#         if payment_status and payment_status.lower() not in ['all', 'none', '']:
#             query = query.filter(Service_Request.status == payment_status.lower())
#             print(f"✅ Payment status filter applied: {payment_status.lower()}")
        
#         # Apply service category filter
#         if service_category and service_category.lower() not in ['all', 'none', '']:
#             if service_category.lower() == 'mobile recharge':
#                 query = query.filter(
#                     Service_Request.service_type.ilike('%mobile%'),
#                     Service_Request.service_type.ilike('%recharge%'),
#                     ~Service_Request.service_type.ilike('%prime%')
#                 )
#             elif service_category.lower() == 'prime activation':
#                 query = query.filter(Service_Request.service_type.ilike('%prime%'))
#             elif service_category.lower() in ['dth', 'd2h', 'dth recharge']:
#                 query = query.filter(
#                     or_(
#                         Service_Request.service_type.ilike('%dth%'),
#                         Service_Request.service_type.ilike('%d2h%')
#                     )
#                 )
#             elif service_category.lower() == 'others':
#                 query = query.filter(
#                     ~Service_Request.service_type.ilike('%mobile%'),
#                     ~Service_Request.service_type.ilike('%prime%'),
#                     ~Service_Request.service_type.ilike('%dth%'),
#                     ~Service_Request.service_type.ilike('%d2h%'),
#                     ~Service_Request.service_type.ilike('%recharge%')
#                 )
#             print(f"✅ Service category filter applied: {service_category}")
        
#         # Get total count
#         total_records = query.count()
#         print(f"📊 Total transactions: {total_records}")
        
#         # Apply pagination
#         offset = (page - 1) * page_size
#         service_requests = query.order_by(desc(Service_Request.created_at)).limit(page_size).offset(offset).all()
        
#         # Get user IDs for batch lookup
#         user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))
        
#         # Batch fetch user details (who initiated the transaction)
#         users_dict = {}
#         if user_ids:
#             users = db.query(User.UserID, User.fullname, User.member_id, User.MobileNumber).filter(
#                 User.UserID.in_(user_ids)
#             ).all()
#             users_dict = {u.UserID: {"name": u.fullname or f"User {u.UserID}", "member_id": u.member_id, "mobile": u.MobileNumber} for u in users}
        
#         # Get prime activation details
#         from models.models import PrimeActivations
#         reference_ids = [sr.reference_id for sr in service_requests if sr.reference_id]
#         prime_activations = {}
        
#         if reference_ids:
#             primes = db.query(PrimeActivations).options(
#                 joinedload(PrimeActivations.receiver_member),
#                 joinedload(PrimeActivations.prime_activator)
#             ).filter(PrimeActivations.reference_id.in_(reference_ids)).all()
#             prime_activations = {p.reference_id: p for p in primes}
#             print(f"✅ Found {len(prime_activations)} prime activations")
        
#         # Get recipient users by mobile number (for mobile/DTH recharge)
#         mobile_numbers = [sr.mobile_number for sr in service_requests if sr.mobile_number]
#         recipient_users = {}
#         if mobile_numbers:
#             recipients = db.query(User).filter(User.MobileNumber.in_(mobile_numbers)).all()
#             recipient_users = {u.MobileNumber: u for u in recipients}
        
#         result = []
#         for sr in service_requests:
#             user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A", "mobile": "N/A"})
            
#             # Determine payment_by and payment_for
#             payment_by = {
#                 "name": user_info["name"],
#                 "member_id": user_info["member_id"],
#                 "mobile": user_info["mobile"]
#             }
            
#             payment_for = None
            
#             # Check for Prime Activation
#             if sr.reference_id in prime_activations:
#                 prime = prime_activations[sr.reference_id]
#                 activated_user = prime.receiver_member
#                 initiator_user = prime.prime_activator
                
#                 payment_by = {
#                     "name": initiator_user.fullname if initiator_user else "Unknown",
#                     "member_id": prime.prime_initiated_by,
#                     "mobile": initiator_user.MobileNumber if initiator_user else "N/A"
#                 }
                
#                 payment_for = {
#                     "name": activated_user.fullname if activated_user else "Unknown",
#                     "member_id": prime.member,
#                     "mobile": activated_user.MobileNumber if activated_user else "N/A",
#                     "type": "Prime Activation"
#                 }
#             # Check for Mobile/DTH Recharge
#             elif sr.mobile_number:
#                 if sr.mobile_number in recipient_users:
#                     recipient = recipient_users[sr.mobile_number]
#                     payment_for = {
#                         "name": recipient.fullname or "Unknown",
#                         "member_id": recipient.member_id,
#                         "mobile": sr.mobile_number,
#                         "type": "Mobile/DTH Recharge"
#                     }
#                 else:
#                     payment_for = {
#                         "name": "External User",
#                         "member_id": "N/A",
#                         "mobile": sr.mobile_number,
#                         "type": "Mobile/DTH Recharge"
#                     }
            
#             result.append({
#                 "id": sr.id,
#                 "user_id": sr.user_id,
#                 "service_type": sr.service_type or "N/A",
#                 "operator_code": sr.operator_code or "N/A",
#                 "mobile_number": sr.mobile_number or "N/A",
#                 "amount": float(sr.amount) if sr.amount else 0.0,
#                 "reference_id": sr.reference_id or "N/A",
#                 "status": sr.status or "unknown",
#                 "payment_txn_id": sr.payment_txn_id or "N/A",
#                 "utr_no": sr.utr_no or "N/A",
#                 "created_at": sr.created_at.isoformat() if sr.created_at else None,
#                 "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
#                 "payment_by": payment_by,
#                 "payment_for": payment_for
#             })
        
#         print(f"✅ Returning {len(result)} transaction records")
        
#         return {
#             "transactions": result,
#             "pagination": {
#                 "current_page": page,
#                 "page_size": page_size,
#                 "total_records": total_records,
#                 "total_pages": (total_records + page_size - 1) // page_size
#             }
#         }
        
#     except Exception as e:
#         print(f"❌ Error in get_bill_transactions: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func
from datetime import datetime
from decimal import Decimal

from core.database import get_db
from core.auth import get_current_user, TokenData
from models.payment_gateway import Payment_Gateway
from models.models import User, LcrMoney, LcrRewards, BillTransactions
from models.service_request import Service_Request

router = APIRouter(tags=["transactions"])

@router.get("/detail/{reference_id}")
async def get_transaction_detail(
    reference_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed transaction info including LCR money and rewards by reference_id"""
    try:
        print(f"🔍 Searching for reference_id: {reference_id}")

        # Find service request by reference_id
        service_req = db.query(Service_Request).filter(
            Service_Request.reference_id == reference_id
        ).first()

        if not service_req:
            print(f"⚠️ No service request found for reference_id: {reference_id}")
            return {
                "reference_id": reference_id,
                "service_type": "N/A",
                "amount": 0,
                "lcr_money": 0,
                "lcr_reward": 0,
                "money_status": "Not Found",
                "reward_status": "Not Found",
                "status": "Not Found",
                "prime_activation": None
            }

        print(f"✅ Found service request: ID={service_req.id}, Status={service_req.status}")

        # Get LCR Money total for this reference_id
        lcr_money_total = db.query(func.sum(LcrMoney.amount)).filter(
            LcrMoney.reference_id == reference_id
        ).scalar() or Decimal('0.00')

        # Get LCR Rewards total for this reference_id
        lcr_reward_total = db.query(func.sum(LcrRewards.amount)).filter(
            LcrRewards.reference_id == reference_id
        ).scalar() or Decimal('0.00')

        print(f"💰 LCR Money Total: {lcr_money_total}, LCR Reward Total: {lcr_reward_total}")

        # Check if this is a Prime Activation transaction
        prime_activation = None
        if service_req.service_type and 'prime' in service_req.service_type.lower():
            from models.models import PrimeActivations, User

            print(f"🔍 Checking for Prime Activation with reference_id: {reference_id}")

            prime_record = db.query(PrimeActivations).options(
                joinedload(PrimeActivations.receiver_member),
                joinedload(PrimeActivations.prime_activator)
            ).filter(
                PrimeActivations.reference_id == reference_id
            ).first()

            if prime_record:
                print(f"✅ Found Prime Activation: member={prime_record.member}, paid_by={prime_record.prime_initiated_by}")

                # Use relationships instead of separate queries
                activated_user = prime_record.receiver_member
                initiator_user = prime_record.prime_activator

                prime_activation = {
                    "activated_member_id": prime_record.member,
                    "activated_member_name": activated_user.fullname if activated_user else "Unknown",
                    "activated_member_mobile": activated_user.MobileNumber if activated_user else "N/A",
                    "paid_by_member_id": prime_record.prime_initiated_by,
                    "paid_by_name": initiator_user.fullname if initiator_user else "Unknown",
                    "paid_by_mobile": initiator_user.MobileNumber if initiator_user else "N/A",
                    "package_amount": float(prime_record.package_amount) if prime_record.package_amount else 0,
                    "activation_date": prime_record.activation_date.isoformat() if prime_record.activation_date else None
                }

                print(f"📦 Prime Activation Details: {prime_activation}")
            else:
                print(f"⚠️ No Prime Activation found for reference_id: {reference_id}")

        # Determine status based on service request status
        is_completed = service_req.status.lower() in ['completed', 'paid', 'success']

        return {
            "reference_id": reference_id,
            "service_type": service_req.service_type or "N/A",
            "amount": float(service_req.amount) if service_req.amount else 0,
            "lcr_money": float(lcr_money_total),
            "lcr_reward": float(lcr_reward_total),
            "money_status": "Credited" if is_completed else "Pending",
            "reward_status": "Credited" if is_completed else "Pending",
            "status": service_req.status,
            "prime_activation": prime_activation
        }

    except Exception as e:
        print(f"❌ Error in get_transaction_detail: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/service-types")
async def get_service_types(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all unique service types"""
    try:
        service_types = db.query(Service_Request.service_type).distinct().all()
        return [st[0] for st in service_types if st[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mobile")
async def get_mobile_transactions(
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(500, le=1000),
    service_type: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get mobile recharge transactions only (excluding Prime, BBPS, DTH)
    Professional query with proper filtering logic
    """
    try:
        # Base query - ONLY mobile recharge services (strict filtering) - including pending status
        query = db.query(Service_Request).filter(
            Service_Request.status.in_(['completed', 'failed', 'processing', 'paid', 'pending']),
            Service_Request.service_type.ilike('%mobile%'),
            Service_Request.service_type.ilike('%recharge%'),
            ~Service_Request.service_type.ilike('%prime%'),
            ~Service_Request.service_type.ilike('%dth%'),
            ~Service_Request.service_type.ilike('%bbps%'),
            ~Service_Request.service_type.ilike('%bill%')
        )

        # Apply service type filter if provided
        if service_type and service_type != 'all':
            query = query.filter(Service_Request.service_type == service_type)

        # Apply status filter if provided
        if status and status != 'all':
            query = query.filter(Service_Request.status == status)

        offset = (page - 1) * limit
        service_requests = query.order_by(desc(Service_Request.created_at)).limit(limit).offset(offset).all()

        # Get user IDs for batch lookup
        user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))

        # Batch fetch user names
        users_dict = {}
        if user_ids:
            users = db.query(User.UserID, User.fullname, User.member_id).filter(
                User.UserID.in_(user_ids)
            ).all()
            users_dict = {u.UserID: {"name": u.fullname or f"User {u.UserID}", "member_id": u.member_id} for u in users}

        result = []
        for sr in service_requests:
            user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A"})

            result.append({
                "id": sr.id,
                "user_id": sr.user_id,
                "user_name": user_info["name"],
                "user_member_id": user_info["member_id"],
                "service_type": sr.service_type or "N/A",
                "operator_code": sr.operator_code,
                "mobile_number": sr.mobile_number,
                "amount": str(sr.amount) if sr.amount else "0",
                "reference_id": sr.reference_id or "N/A",
                "status": sr.status or "unknown",
                "payment_txn_id": sr.payment_txn_id,
                "utr_no": sr.utr_no,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
                "updated_at": sr.updated_at.isoformat() if sr.updated_at else None
            })

        # Fetch total count for pagination metadata
        total_records = query.count()

        return {
            "transactions": result,
            "pagination": {
                "current_page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-details/{reference_id}")
async def get_payment_details(
    reference_id: str,
    current_user: TokenData = Depends(get_current_user),
    lcr_money_page: int = Query(1, ge=1),
    lcr_rewards_page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=10, le=50),
    db: Session = Depends(get_db)
):
    """
    Get complete payment details for a reference ID
    Uses reference_id to JOIN service_request, lcrmoney, and lcr_rewards tables
    Professional implementation with optimized queries
    """
    try:
        # Primary query - get service request by reference_id
        service_request = (
            db.query(Service_Request)
            .filter(Service_Request.reference_id == reference_id)
            .first()
        )

        if not service_request:
            raise HTTPException(status_code=404, detail=f"Service request not found for reference_id: {reference_id}")

        # Get user details - optimized single query
        user = db.query(
            User.UserID, User.fullname, User.MobileNumber, User.Email, User.member_id
        ).filter(User.UserID == service_request.user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Payment Gateway transactions - related to this service request
        payments = db.query(Payment_Gateway).filter(
            Payment_Gateway.service_request_id == service_request.id
        ).order_by(desc(Payment_Gateway.created_at)).limit(10).all()

        # LCR Money - JOIN by reference_id (PRIMARY) + user_id fallback
        lcr_money_offset = (lcr_money_page - 1) * page_size
        lcr_money_query = db.query(LcrMoney).filter(
            LcrMoney.reference_id == reference_id
        )

        lcr_money = lcr_money_query.order_by(
            desc(LcrMoney.transactiondate)
        ).limit(page_size).offset(lcr_money_offset).all()

        lcr_money_total = lcr_money_query.count()

        # Calculate total distributed LCRmoney
        lcr_money_total_amount = db.query(func.sum(LcrMoney.amount)).filter(
            LcrMoney.reference_id == reference_id
        ).scalar() or Decimal('0.00000')

        # LCR Rewards - JOIN by reference_id (PRIMARY) + user_id fallback
        lcr_rewards_offset = (lcr_rewards_page - 1) * page_size
        lcr_rewards_query = db.query(LcrRewards).filter(
            LcrRewards.reference_id == reference_id
        )

        lcr_rewards = lcr_rewards_query.order_by(
            desc(LcrRewards.transactiondate)
        ).limit(page_size).offset(lcr_rewards_offset).all()

        lcr_rewards_total = lcr_rewards_query.count()

        # Calculate total distributed LCR_rewards
        lcr_rewards_total_amount = db.query(func.sum(LcrRewards.amount)).filter(
            LcrRewards.reference_id == reference_id
        ).scalar() or Decimal('0.00000')

        return {
            "service_request": {
                "id": service_request.id,
                "reference_id": service_request.reference_id,
                "service_type": service_request.service_type,
                "operator_code": service_request.operator_code,
                "mobile_number": service_request.mobile_number,
                "amount": float(service_request.amount),
                "status": service_request.status,
                "payment_txn_id": service_request.payment_txn_id,
                "utr_no": service_request.utr_no,
                "created_at": service_request.created_at.isoformat() if service_request.created_at else None,
                "updated_at": service_request.updated_at.isoformat() if service_request.updated_at else None,
                "metadata": service_request.service_metadata
            },
            "user": {
                "id": user.UserID if user else None,
                "name": user.fullname if user else "Unknown",
                "mobile": user.MobileNumber if user else "N/A",
                "email": user.Email if user else "N/A",
                "member_id": user.member_id if user else "N/A"
            },
            "payment_gateway_transactions": [
                {
                    "id": pg.id,
                    "client_txn_id": pg.client_txn_id,
                    "sabpaisa_txn_id": pg.sabpaisa_txn_id,
                    "payer_name": pg.payer_name,
                    "payer_email": pg.payer_email,
                    "payer_mobile": pg.payer_mobile,
                    "amount": float(pg.amount) if pg.amount else 0,
                    "paid_amount": float(pg.paid_amount) if pg.paid_amount else 0,
                    "payment_mode": pg.payment_mode,
                    "bank_name": pg.bank_name,
                    "rrn": pg.rrn,
                    "purpose": pg.purpose,
                    "status": pg.status,
                    "status_code": pg.status_code,
                    "sabpaisa_message": pg.sabpaisa_message,
                    "service_data": pg.service_data,
                    "amount_type": pg.amount_type,
                    "challan_number": pg.challan_number,
                    "bank_error_code": pg.bank_error_code,
                    "sabpaisa_error_code": pg.sabpaisa_error_code,
                    "trans_date": pg.trans_date.isoformat() if pg.trans_date else None,
                    "created_at": pg.created_at.isoformat() if pg.created_at else None,
                    "updated_at": pg.updated_at.isoformat() if pg.updated_at else None
                }
                for pg in payments
            ],
            "lcr_money_transactions": [
                {
                    "id": lm.srno,
                    "amount": float(lm.amount) if lm.amount else 0.0,
                    "type": lm.transactiontype or "N/A",
                    "received_by": lm.received_by or "N/A",
                    "received_from": lm.received_from or "N/A",
                    "status": "Active" if lm.status == 1 else "Inactive",
                    "date": lm.transactiondate.strftime('%Y-%m-%d') if lm.transactiondate else "N/A",
                    "time": lm.transactiondate.strftime('%H:%M:%S') if lm.transactiondate else "N/A",
                    "purpose": lm.purpose or "N/A",
                    "remark": lm.remark or "N/A"
                }
                for lm in lcr_money
            ],
            "lcr_rewards_transactions": [
                {
                    "id": lr.srno,
                    "amount": float(lr.amount) if lr.amount else 0.0,
                    "type": lr.transactiontype or "N/A",
                    "received_by": lr.received_by or "N/A",
                    "received_from": lr.received_from or "N/A",
                    "status": "Active" if lr.status == 1 else "Inactive",
                    "date": lr.transactiondate.strftime('%Y-%m-%d') if lr.transactiondate else "N/A",
                    "time": lr.transactiondate.strftime('%H:%M:%S') if lr.transactiondate else "N/A",
                    "purpose": lr.purpose or "N/A",
                    "remark": lr.remark or "N/A"
                }
                for lr in lcr_rewards
            ],
            "pagination": {
                "lcr_money": {
                    "current_page": lcr_money_page,
                    "page_size": page_size,
                    "total_records": lcr_money_total,
                    "total_pages": (lcr_money_total + page_size - 1) // page_size
                },
                "lcr_rewards": {
                    "current_page": lcr_rewards_page,
                    "page_size": page_size,
                    "total_records": lcr_rewards_total,
                    "total_pages": (lcr_rewards_total + page_size - 1) // page_size
                }
            },
            "totals": {
                "lcr_money_distributed": float(lcr_money_total_amount),
                "lcr_rewards_distributed": float(lcr_rewards_total_amount)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dth")
async def get_dth_transactions(
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(100, le=500),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Get DTH recharge transactions"""
    try:
        query = db.query(Payment_Gateway).join(
            User, Payment_Gateway.payer_mobile == User.MobileNumber
        ).filter(
            Payment_Gateway.purpose.ilike('%dth%')
        )

        offset = (page - 1) * limit
        transactions = query.order_by(desc(Payment_Gateway.created_at)).limit(limit).offset(offset).all()

        result = []
        for txn in transactions:
            user = db.query(User).filter(User.MobileNumber == txn.payer_mobile).first()
            result.append({
                "id": txn.id,
                "transactionId": f"DTH{txn.id:06d}",
                "user": txn.payer_name or (user.fullname if user else "Unknown"),
                "subscriberId": txn.service_data.get('subscriber_id', f"SUB{txn.id}") if txn.service_data else f"SUB{txn.id}",
                "operator": txn.service_data.get('operator', 'Unknown') if txn.service_data else 'Unknown',
                "plan": txn.service_data.get('plan', 'Standard') if txn.service_data else 'Standard',
                "amount": float(txn.amount) if txn.amount else 0,
                "status": "Success" if txn.status == "success" else "Pending" if txn.status == "pending" else "Failed",
                "date": txn.created_at.strftime('%Y-%m-%d') if txn.created_at else "",
                "time": txn.created_at.strftime('%H:%M:%S') if txn.created_at else "",
                "referenceId": txn.rrn or f"REF{txn.id}"
            })

        total_records = query.count()

        return {
            "transactions": result,
            "pagination": {
                "current_page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/other")
async def get_other_transactions(
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(500, le=1000),
    service_type: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get other service transactions (Prime Activation, BBPS, etc.)
    Excludes Mobile Recharge and DTH - Professional implementation
    """
    try:
        # Base query - Prime Activation, BBPS and other services - including pending status
        # EXCLUDE mobile recharge and DTH completely
        query = db.query(Service_Request).filter(
            Service_Request.status.in_(['completed', 'failed', 'processing', 'paid', 'pending']),
            or_(
                Service_Request.service_type.ilike('%prime%'),
                Service_Request.service_type.ilike('%bbps%'),
                Service_Request.service_type.ilike('%bill%')
            ),
            ~Service_Request.service_type.ilike('%mobile%'),
            ~Service_Request.service_type.ilike('%dth%')
        )

        # Apply service type filter if provided
        if service_type and service_type != 'all':
            query = query.filter(Service_Request.service_type == service_type)

        # Apply status filter if provided
        if status and status != 'all':
            query = query.filter(Service_Request.status == status)

        offset = (page - 1) * limit
        service_requests = query.order_by(desc(Service_Request.created_at)).limit(limit).offset(offset).all()

        # Get user IDs for batch lookup
        user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))

        # Batch fetch user names
        users_dict = {}
        if user_ids:
            users = db.query(User.UserID, User.fullname, User.member_id).filter(
                User.UserID.in_(user_ids)
            ).all()
            users_dict = {u.UserID: {"name": u.fullname or f"User {u.UserID}", "member_id": u.member_id} for u in users}

        result = []
        for sr in service_requests:
            user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A"})

            result.append({
                "id": sr.id,
                "user_id": sr.user_id,
                "user_name": user_info["name"],
                "user_member_id": user_info["member_id"],
                "service_type": sr.service_type or "Other Service",
                "operator_code": sr.operator_code,
                "mobile_number": sr.mobile_number,
                "amount": str(sr.amount) if sr.amount else "0",
                "reference_id": sr.reference_id or "N/A",
                "status": sr.status or "unknown",
                "payment_txn_id": sr.payment_txn_id,
                "utr_no": sr.utr_no,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
                "updated_at": sr.updated_at.isoformat() if sr.updated_at else None
            })

        total_records = query.count()

        return {
            "transactions": result,
            "pagination": {
                "current_page": page,
                "page_size": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/all")
async def get_user_all_transactions(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transactions for a specific user - Service Requests + LCR Money + LCR Rewards (joined by reference_id)"""
    try:
        # Get user details
        user = db.query(User).filter(User.UserID == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Service Requests (excluding pending)
        service_requests = db.query(Service_Request).filter(
            Service_Request.user_id == user_id,
            Service_Request.status != 'pending'
        ).order_by(desc(Service_Request.created_at)).all()

        # Get all reference_ids for joining
        service_reference_ids = [sr.reference_id for sr in service_requests if sr.reference_id]

        # Get all mobile numbers from service requests to look up recipient users
        mobile_numbers = [sr.mobile_number for sr in service_requests if sr.mobile_number]

        # Batch lookup: Find users by mobile numbers (who was recharged)
        recipient_users = {}
        if mobile_numbers:
            recipients = db.query(User).filter(User.MobileNumber.in_(mobile_numbers)).all()
            recipient_users = {u.MobileNumber: u for u in recipients}

        # Batch lookup: Find prime activation details by reference_id
        from models.models import PrimeActivations
        prime_activations = {}
        prime_member_ids = set()
        if service_reference_ids:
            primes = db.query(PrimeActivations).filter(
                PrimeActivations.reference_id.in_(service_reference_ids)
            ).all()
            prime_activations = {p.reference_id: p for p in primes}
            prime_member_ids = {p.member for p in primes if p.member}

        # Batch lookup: Find users by member IDs for prime activations
        prime_recipients = {}
        if prime_member_ids:
            prime_users = db.query(User).filter(User.member_id.in_(prime_member_ids)).all()
            prime_recipients = {u.member_id: u for u in prime_users}

        # LCR Bones - joined by reference_id
        lcr_bones = []
        if service_reference_ids:
            lcr_bones = db.query(LcrMoney).filter(
                LcrMoney.reference_id.in_(service_reference_ids)
            ).order_by(desc(LcrMoney.transactiondate)).all()

        # LCR Rewards - joined by reference_id
        lcr_rewards = []
        if service_reference_ids:
            lcr_rewards = db.query(LcrRewards).filter(
                LcrRewards.reference_id.in_(service_reference_ids)
            ).order_by(desc(LcrRewards.transactiondate)).all()

        # Build service requests with recipient info
        service_requests_data = []
        for sr in service_requests:
            recipient_info = None

            # Check if this is a prime activation (check first as it's more specific)
            if sr.reference_id and sr.reference_id in prime_activations:
                prime = prime_activations[sr.reference_id]
                # Get the member who received prime from pre-loaded dict
                if prime.member and prime.member in prime_recipients:
                    prime_recipient = prime_recipients[prime.member]
                    recipient_info = {
                        "type": "prime_activation",
                        "user_id": prime_recipient.UserID,
                        "name": prime_recipient.fullname or f"User {prime_recipient.UserID}",
                        "member_id": prime_recipient.member_id,
                        "mobile": prime_recipient.MobileNumber
                    }

            # Check if this is a mobile recharge to another user (not self)
            elif sr.mobile_number and sr.mobile_number != user.MobileNumber and sr.mobile_number in recipient_users:
                recipient = recipient_users[sr.mobile_number]
                recipient_info = {
                    "type": "mobile_recharge",
                    "user_id": recipient.UserID,
                    "name": recipient.fullname or f"User {recipient.UserID}",
                    "member_id": recipient.member_id,
                    "mobile": recipient.MobileNumber
                }

            # Check if user recharged their own number
            elif sr.mobile_number and sr.mobile_number == user.MobileNumber:
                recipient_info = {
                    "type": "mobile_recharge",
                    "user_id": user.UserID,
                    "name": user.fullname or f"User {user.UserID}",
                    "member_id": user.member_id,
                    "mobile": user.MobileNumber
                }

            # If mobile number but no user found, show as external
            elif sr.mobile_number:
                recipient_info = {
                    "type": "external_mobile",
                    "mobile": sr.mobile_number,
                    "name": "External User"
                }

            service_requests_data.append({
                "id": sr.id,
                "reference_id": sr.reference_id,
                "service_type": sr.service_type,
                "operator": sr.operator_code or "N/A",
                "mobile": sr.mobile_number or "N/A",
                "amount": float(sr.amount),
                "status": sr.status.capitalize(),
                "payment_txn_id": sr.payment_txn_id or "N/A",
                "utr_no": sr.utr_no or "N/A",
                "date": sr.created_at.strftime('%Y-%m-%d'),
                "time": sr.created_at.strftime('%H:%M:%S'),
                "recipient": recipient_info  # NEW: Who was recharged or whose prime was activated
            })

        return {
            "user": {
                "id": user.UserID,
                "name": user.fullname,
                "member_id": user.member_id,
                "mobile": user.MobileNumber
            },
            "service_requests": service_requests_data,
            "lcr_bones": [
                {
                    "id": lb.srno,
                    "reference_id": lb.reference_id or "N/A",
                    "amount": float(lb.amount) if lb.amount else 0.0,
                    "type": lb.transactiontype or "N/A",
                    "received_by": lb.received_by or "N/A",
                    "received_from": lb.received_from or "N/A",
                    "status": "Active" if lb.status == 1 else "Inactive",
                    "date": lb.transactiondate.strftime('%Y-%m-%d') if lb.transactiondate else "N/A",
                    "time": lb.transactiondate.strftime('%H:%M:%S') if lb.transactiondate else "N/A",
                    "purpose": lb.purpose or "N/A",
                    "remark": lb.remark or "N/A"
                }
                for lb in lcr_bones
            ],
            "lcr_rewards": [
                {
                    "id": lr.srno,
                    "reference_id": lr.reference_id or "N/A",
                    "amount": float(lr.amount) if lr.amount else 0.0,
                    "type": lr.transactiontype or "N/A",
                    "received_by": lr.received_by or "N/A",
                    "received_from": lr.received_from or "N/A",
                    "status": "Active" if lr.status == 1 else "Inactive",
                    "date": lr.transactiondate.strftime('%Y-%m-%d') if lr.transactiondate else "N/A",
                    "time": lr.transactiondate.strftime('%H:%M:%S') if lr.transactiondate else "N/A",
                    "purpose": lr.purpose or "N/A",
                    "remark": lr.remark or "N/A"
                }
                for lr in lcr_rewards
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Placeholder for Matrix Level Menu and its related logic
@router.get("/matrix-levels")
async def get_matrix_levels(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    This endpoint will provide data for the Matrix Level Menu.
    It will group users into levels (L1-L10, L11-L20, etc.)
    and display their status.
    Pagination will be applied for large datasets.
    """
    # TODO: Implement logic to query users, determine their level, and return paginated results.
    # This will involve complex SQL queries or data processing.
    # Example: Fetch all users, then process them to determine their level based on criteria.
    # For now, returning a placeholder response.
    raise HTTPException(status_code=501, detail="Matrix Level functionality not yet implemented.")


@router.get("/all-records")
async def get_all_records(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, le=500),
    status: str = Query(None),
    service_type: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    search: str = Query(None),
    reference_id: str = Query(None)
):
    """
    Fetches ALL records from Service_Request with ALL statuses
    Optimized for performance with proper pagination
    Supports filtering by status and service_type
    Shows who paid to whom for each transaction
    """
    try:
        print(f"📊 [API] /all-records called - Filters: status={status}, service_type={service_type}, start_date={start_date}, end_date={end_date}, search={search}, reference_id={reference_id}, page={page}, page_size={page_size}")
        
        # Base query - Include ALL statuses with optimized loading
        query = db.query(Service_Request)

        # Apply date filter (highest priority)
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Service_Request.created_at >= start_dt)
                print(f"✅ Start date filter applied: {start_date}")
            except ValueError:
                print(f"⚠️ Invalid start_date format: {start_date}")

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                # Add one day to include the full end_date
                from datetime import timedelta
                end_dt_inclusive = end_dt + timedelta(days=1)
                query = query.filter(Service_Request.created_at < end_dt_inclusive)
                print(f"✅ End date filter applied: {end_date} (inclusive)")
            except ValueError:
                print(f"⚠️ Invalid end_date format: {end_date}")

        # Apply status filter (second priority)
        if status and status.lower() not in ['all', 'none', '']:
            query = query.filter(Service_Request.status == status.lower())
            print(f"✅ Status filter applied: {status.lower()}")

        # Apply service type filter
        if service_type and service_type.lower() not in ['all', 'none', '']:
            if service_type.lower() == 'mobile recharge':
                query = query.filter(
                    Service_Request.service_type.ilike('%mobile%'),
                    Service_Request.service_type.ilike('%recharge%'),
                    ~Service_Request.service_type.ilike('%prime%')
                )
            elif service_type.lower() == 'prime activation':
                query = query.filter(Service_Request.service_type.ilike('%prime%'))
            elif service_type.lower() in ['dth recharge', 'd2h recharge', 'dth services']:
                query = query.filter(
                    or_(
                        Service_Request.service_type.ilike('%dth%'),
                        Service_Request.service_type.ilike('%d2h%')
                    )
                )
            elif service_type.lower() == 'others':
                query = query.filter(
                    ~Service_Request.service_type.ilike('%mobile%'),
                    ~Service_Request.service_type.ilike('%prime%'),
                    ~Service_Request.service_type.ilike('%dth%'),
                    ~Service_Request.service_type.ilike('%d2h%'),
                    ~Service_Request.service_type.ilike('%recharge%')
                )
            print(f"✅ Service type filter applied: {service_type}")

        # Apply search filter (reference_id, mobile_number, user details)
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Service_Request.reference_id.ilike(search_term),
                    Service_Request.mobile_number.ilike(search_term),
                    Service_Request.payment_txn_id.ilike(search_term),
                    Service_Request.utr_no.ilike(search_term)
                )
            )
            print(f"✅ Search filter applied: {search.strip()}")

        # Apply reference_id filter (exact match)
        if reference_id and reference_id.strip():
            query = query.filter(Service_Request.reference_id == reference_id.strip())
            print(f"✅ Reference ID filter applied: {reference_id.strip()}")

        # Get total count before pagination
        total_records = query.count()
        print(f"📊 Total records matching filters: {total_records}")

        # Apply pagination
        offset = (page - 1) * page_size
        service_requests = query.order_by(desc(Service_Request.created_at)).limit(page_size).offset(offset).all()

        # Get user IDs for batch lookup
        user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))

        # Batch fetch user details (who initiated the transaction)
        users_dict = {}
        if user_ids:
            users = db.query(User.UserID, User.fullname, User.member_id, User.MobileNumber).filter(
                User.UserID.in_(user_ids)
            ).all()
            
            print(f"🔍 DEBUG: Fetched {len(users)} users from database")
            for u in users:
                print(f"🔍 DEBUG: User {u.UserID} - Name: '{u.fullname}', Member: '{u.member_id}', Mobile: '{u.MobileNumber}'")
            
            # Fetch user addresses
            from models.models import User_Aadhar_Address, Aadhar_User
            aadhar_user_ids = [u.UserID for u in users]
            user_addresses = {}
            if aadhar_user_ids:
                aadhar_users = db.query(Aadhar_User).filter(
                    Aadhar_User.user_id.in_(aadhar_user_ids)
                ).all()
                address_ids = [au.address_id for au in aadhar_users if au.address_id]
                
                if address_ids:
                    addresses = db.query(User_Aadhar_Address).filter(
                        User_Aadhar_Address.id.in_(address_ids)
                    ).all()
                    user_addresses = {addr.id: addr for addr in addresses}
            
            users_dict = {u.UserID: {
                "name": u.fullname or f"User {u.UserID}", 
                "member_id": u.member_id, 
                "mobile": u.MobileNumber,
                "address": None
            } for u in users}
            
            # Map addresses to users
            for aadhar_user in aadhar_users:
                if hasattr(aadhar_user, 'address_id') and aadhar_user.address_id in user_addresses:
                    address = user_addresses[aadhar_user.address_id]
                    if aadhar_user.user_id in users_dict:
                        # Format complete address
                        address_parts = []
                        if address.house and address.house.strip() and address.house.strip() != '-':
                            address_parts.append(address.house.strip())
                        if address.street and address.street.strip() and address.street.strip() != '-':
                            address_parts.append(address.street.strip())
                        if address.locality and address.locality.strip() and address.locality.strip() != '-':
                            address_parts.append(address.locality.strip())
                        if address.landmark and address.landmark.strip() and address.landmark.strip() != '-':
                            address_parts.append(address.landmark.strip())
                        if address.vtc and address.vtc.strip() and address.vtc.strip() != '-':
                            address_parts.append(address.vtc.strip())
                        if address.subDistrict and address.subDistrict.strip() and address.subDistrict.strip() != '-':
                            address_parts.append(address.subDistrict.strip())
                        if address.district and address.district.strip() and address.district.strip() != '-':
                            address_parts.append(address.district.strip())
                        if address.state and address.state.strip() and address.state.strip() != '-':
                            address_parts.append(address.state.strip())
                        if address.pin and address.pin.strip() and address.pin.strip() != '-':
                            address_parts.append(address.pin.strip())
                        if address.country and address.country.strip() and address.country.strip() != '-':
                            address_parts.append(address.country.strip())
                        
                        # Update existing user dict with address, preserve name
                        users_dict[aadhar_user.user_id]["address"] = ", ".join(filter(None, address_parts))

        # Get prime activation details
        from models.models import PrimeActivations
        reference_ids = [sr.reference_id for sr in service_requests if sr.reference_id]
        prime_activations = {}
        prime_member_ids = set()
        
        if reference_ids:
            primes = db.query(PrimeActivations).options(
                joinedload(PrimeActivations.receiver_member),
                joinedload(PrimeActivations.prime_activator)
            ).filter(PrimeActivations.reference_id.in_(reference_ids)).all()
            prime_activations = {p.reference_id: p for p in primes}
            print(f"✅ Found {len(prime_activations)} prime activations")

        # Get recipient users by mobile number (for mobile recharge)
        mobile_numbers = [sr.mobile_number for sr in service_requests if sr.mobile_number]
        recipient_users = {}
        if mobile_numbers:
            recipients = db.query(User).filter(User.MobileNumber.in_(mobile_numbers)).all()
            recipient_users = {u.MobileNumber: u for u in recipients}

        result = []
        for sr in service_requests:
            user_info = users_dict.get(sr.user_id, {"name": f"User {sr.user_id}", "member_id": "N/A", "mobile": "N/A"})

            # Determine payment_by and payment_for
            payment_by = {
                "name": user_info["name"],
                "member_id": user_info["member_id"],
                "mobile": user_info["mobile"]
            }
            
            payment_for = None
            prime_data = None

            # Check for Prime Activation (highest priority)
            if sr.reference_id in prime_activations:
                prime = prime_activations[sr.reference_id]
                activated_user = prime.receiver_member
                initiator_user = prime.prime_activator
                
                # Payment BY is the initiator
                payment_by = {
                    "name": initiator_user.fullname if initiator_user else "Unknown",
                    "member_id": prime.prime_initiated_by,
                    "mobile": initiator_user.MobileNumber if initiator_user else "N/A"
                }
                
                # Payment FOR is the receiver
                payment_for = {
                    "name": activated_user.fullname if activated_user else "Unknown",
                    "member_id": prime.member,
                    "mobile": activated_user.MobileNumber if activated_user else "N/A",
                    "type": "Prime Activation"
                }
                
                prime_data = {
                    "activated_member_id": prime.member,
                    "activated_member_name": activated_user.fullname if activated_user else "Unknown",
                    "activated_member_mobile": activated_user.MobileNumber if activated_user else "N/A",
                    "paid_by_member_id": prime.prime_initiated_by,
                    "paid_by_name": initiator_user.fullname if initiator_user else "Unknown",
                    "paid_by_mobile": initiator_user.MobileNumber if initiator_user else "N/A",
                    "package_amount": float(prime.package_amount) if prime.package_amount else 0,
                    "activation_date": prime.activation_date.isoformat() if prime.activation_date else None
                }
            
            # Check for Mobile/DTH Recharge
            elif sr.mobile_number:
                # Check if recipient is a registered user
                if sr.mobile_number in recipient_users:
                    recipient = recipient_users[sr.mobile_number]
                    payment_for = {
                        "name": recipient.fullname or "Unknown",
                        "member_id": recipient.member_id,
                        "mobile": sr.mobile_number,
                        "type": "Mobile/DTH Recharge"
                    }
                else:
                    # External number (not a registered user)
                    payment_for = {
                        "name": "External User",
                        "member_id": "N/A",
                        "mobile": sr.mobile_number,
                        "type": "Mobile/DTH Recharge"
                    }

            result.append({
                "id": sr.id,
                "user_id": sr.user_id,
                "user_name": user_info["name"],
                "user_member_id": user_info["member_id"],
                "user_mobile": user_info["mobile"],
                "user_address": user_info.get("address"),  # Add user address
                "service_type": sr.service_type or "N/A",
                "operator_code": sr.operator_code,
                "mobile_number": sr.mobile_number,
                "amount": str(sr.amount) if sr.amount else "0",
                "reference_id": sr.reference_id or "N/A",
                "status": sr.status or "unknown",
                "payment_txn_id": sr.payment_txn_id,
                "utr_no": sr.utr_no,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
                "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
                "payment_by": payment_by,  # Who paid
                "payment_for": payment_for,  # Who received the service
                "prime_activation": prime_data
            })

        print(f"✅ Returning {len(result)} records")

        return {
            "transactions": result,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": (total_records + page_size - 1) // page_size
            }
        }

    except Exception as e:
        print(f"❌ Error in get_all_records: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{reference_id}")
async def get_transaction_history(
    reference_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete transaction history for a reference_id
    Returns Service_Request + LCR Money + LCR Rewards linked by reference_id
    """
    try:
        print(f"📊 [API] /history/{reference_id} called")
        
        # Fetch LCR Money transactions
        lcr_money_records = db.query(LcrMoney).filter(
            LcrMoney.reference_id == reference_id
        ).all()
        
        # Fetch LCR Rewards transactions
        lcr_rewards_records = db.query(LcrRewards).filter(
            LcrRewards.reference_id == reference_id
        ).all()
        
        # Format LCR Money
        lcr_money_data = []
        for lm in lcr_money_records:
            lcr_money_data.append({
                "srno": lm.srno,
                "amount": float(lm.amount) if lm.amount else 0.0,
                "transaction_type": lm.transactiontype or "N/A",
                "received_by": lm.received_by or "N/A",
                "received_from": lm.received_from or "N/A",
                "received_for": lm.received_for or "N/A",
                "purpose": lm.purpose or "N/A",
                "remark": lm.remark or "N/A",
                "transaction_date": lm.transactiondate.isoformat() if lm.transactiondate else None,
                "status": lm.status,
                "validity": lm.validity.isoformat() if lm.validity else None
            })
        
        # Format LCR Rewards
        lcr_rewards_data = []
        for lr in lcr_rewards_records:
            lcr_rewards_data.append({
                "srno": lr.srno,
                "amount": float(lr.amount) if lr.amount else 0.0,
                "transaction_type": lr.transactiontype or "N/A",
                "received_by": lr.received_by or "N/A",
                "received_from": lr.received_from or "N/A",
                "received_for": lr.received_for or "N/A",
                "purpose": lr.purpose or "N/A",
                "remark": lr.remark or "N/A",
                "transaction_date": lr.transactiondate.isoformat() if lr.transactiondate else None,
                "status": lr.status,
                "validity": lr.validity.isoformat() if lr.validity else None
            })
        
        print(f"✅ Found {len(lcr_money_data)} LCR Money records and {len(lcr_rewards_data)} LCR Rewards records")
        
        return {
            "reference_id": reference_id,
            "lcr_money": lcr_money_data,
            "lcr_rewards": lcr_rewards_data
        }
        
    except Exception as e:
        print(f"❌ Error in get_transaction_history: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transaction-record")
async def get_transaction_record(
    # current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, le=500),
    status: str = Query(None),
    service_type: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    """
    Consolidated Transaction Record API
    Links: Service_Request + Payment_Gateway + BBPS_Bill_Payment_Transactions
    Calculates: LCR Money Applied, LCR Reward Applied, Net Service Value
    
    Returns unified transaction data for frontend display
    """
    try:
        print(f"📊 [API] /transaction-record called - page={page}, page_size={page_size}")
        
        # Base query - Join Service_Request with Payment_Gateway
        query = db.query(Service_Request).outerjoin(
            Payment_Gateway,
            Service_Request.id == Payment_Gateway.service_request_id
        )
        
        # Apply filters
        if status and status.lower() not in ['all', 'none', '']:
            query = query.filter(Service_Request.status == status.lower())
        
        if service_type and service_type.lower() not in ['all', 'none', '']:
            if service_type.lower() == 'bbps':
                query = query.filter(Service_Request.service_type.ilike('%bbps%'))
            elif service_type.lower() == 'mobile recharge':
                query = query.filter(
                    Service_Request.service_type.ilike('%mobile%'),
                    Service_Request.service_type.ilike('%recharge%')
                )
            elif service_type.lower() == 'prime activation':
                query = query.filter(Service_Request.service_type.ilike('%prime%'))
            elif service_type.lower() == 'dth recharge':
                query = query.filter(
                    or_(
                        Service_Request.service_type.ilike('%dth%'),
                        Service_Request.service_type.ilike('%d2h%')
                    )
                )
            elif service_type.lower() == 'others':
                query = query.filter(
                    ~Service_Request.service_type.ilike('%bbps%'),
                    ~Service_Request.service_type.ilike('%mobile%'),
                    ~Service_Request.service_type.ilike('%prime%'),
                    ~Service_Request.service_type.ilike('%dth%'),
                    ~Service_Request.service_type.ilike('%d2h%')
                )
            query = query.filter(Service_Request.created_at >= start_date)
        if end_date:
            query = query.filter(Service_Request.created_at <= end_date)
        
        # Get total count
        total_records = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        service_requests = query.order_by(desc(Service_Request.created_at)).limit(page_size).offset(offset).all()
        
        # Get reference_ids for batch LCR queries
        reference_ids = [sr.reference_id for sr in service_requests if sr.reference_id]
        
        # Batch fetch LCR Money totals by reference_id
        lcr_money_totals = {}
        if reference_ids:
            lcr_money_query = db.query(
                LcrMoney.reference_id,
                func.sum(LcrMoney.amount).label('total')
            ).filter(
                LcrMoney.reference_id.in_(reference_ids)
            ).group_by(LcrMoney.reference_id).all()
            
            lcr_money_totals = {lm.reference_id: float(lm.total) if lm.total else 0.0 for lm in lcr_money_query}
        
        # Batch fetch LCR Rewards totals by reference_id
        lcr_rewards_totals = {}
        if reference_ids:
            lcr_rewards_query = db.query(
                LcrRewards.reference_id,
                func.sum(LcrRewards.amount).label('total')
            ).filter(
                LcrRewards.reference_id.in_(reference_ids)
            ).group_by(LcrRewards.reference_id).all()
            
            lcr_rewards_totals = {lr.reference_id: float(lr.total) if lr.total else 0.0 for lr in lcr_rewards_query}
        
        # Batch fetch BBPS transactions by reference_id
        bbps_transactions = {}
        if reference_ids:
            bbps_records = db.query(BillTransactions).filter(
                BillTransactions.reference_id.in_(reference_ids)
            ).all()
            bbps_transactions = {bt.reference_id: bt for bt in bbps_records}
        
        # Batch fetch user details
        user_ids = list(set([sr.user_id for sr in service_requests if sr.user_id]))
        users_dict = {}
        if user_ids:
            users = db.query(User.UserID, User.fullname, User.member_id, User.MobileNumber).filter(
                User.UserID.in_(user_ids)
            ).all()
            users_dict = {u.UserID: {
                "name": u.fullname or f"User {u.UserID}",
                "member_id": u.member_id,
                "mobile": u.MobileNumber
            } for u in users}
        
        # Build consolidated response
        result = []
        for sr in service_requests:
            user_info = users_dict.get(sr.user_id, {"name": "Unknown", "member_id": "N/A", "mobile": "N/A"})
            
            # Get payment gateway info
            payment_gateway = sr.payments[0] if sr.payments else None
            
            # Get BBPS info if applicable
            bbps_info = bbps_transactions.get(sr.reference_id) if sr.reference_id else None
            
            # Calculate LCR values
            lcr_money_applied = lcr_money_totals.get(sr.reference_id, 0.0)
            lcr_reward_applied = lcr_rewards_totals.get(sr.reference_id, 0.0)
            
            # Calculate Net Service Value
            service_amount = float(sr.amount) if sr.amount else 0.0
            net_service_value = service_amount - lcr_money_applied - lcr_reward_applied
            
            record = {
                # Service Request Fields (Non-duplicate)
                "id": sr.id,
                "reference_id": sr.reference_id or "N/A",
                "service_type": sr.service_type or "N/A",
                "operator_code": sr.operator_code or "N/A",
                "mobile_number": sr.mobile_number or "N/A",
                "service_amount": service_amount,
                "service_status": sr.status or "unknown",
                "service_metadata": sr.service_metadata,
                "created_at": sr.created_at.isoformat() if sr.created_at else None,
                "updated_at": sr.updated_at.isoformat() if sr.updated_at else None,
                
                # User Information
                "user_id": sr.user_id,
                "user_name": user_info["name"],
                "user_member_id": user_info["member_id"],
                "user_mobile": user_info["mobile"],
                
                # Payment Gateway Fields (if exists)
                "payment_gateway_id": payment_gateway.id if payment_gateway else None,
                "payer_name": payment_gateway.payer_name if payment_gateway else None,
                "payer_email": payment_gateway.payer_email if payment_gateway else None,
                "payer_mobile": payment_gateway.payer_mobile if payment_gateway else None,
                "client_txn_id": payment_gateway.client_txn_id if payment_gateway else None,
                "sabpaisa_txn_id": payment_gateway.sabpaisa_txn_id if payment_gateway else sr.payment_txn_id,
                "payment_amount": float(payment_gateway.amount) if payment_gateway and payment_gateway.amount else service_amount,
                "paid_amount": float(payment_gateway.paid_amount) if payment_gateway and payment_gateway.paid_amount else None,
                "payment_mode": payment_gateway.payment_mode if payment_gateway else None,
                "bank_name": payment_gateway.bank_name if payment_gateway else None,
                "rrn": payment_gateway.rrn if payment_gateway else sr.utr_no,
                "payment_purpose": payment_gateway.purpose if payment_gateway else None,
                "payment_status": payment_gateway.status if payment_gateway else sr.status,
                "status_code": payment_gateway.status_code if payment_gateway else None,
                "sabpaisa_message": payment_gateway.sabpaisa_message if payment_gateway else None,
                "trans_date": payment_gateway.trans_date.isoformat() if payment_gateway and payment_gateway.trans_date else None,
                
                # BBPS Bill Payment Fields (if applicable)
                "bbps_id": bbps_info.id if bbps_info else None,
                "bbps_service_name": bbps_info.bbps_service_name if bbps_info else None,
                "bill_payment_reference_no": bbps_info.bill_paymet_reference_no if bbps_info else None,
                "bbps_reference_no": bbps_info.bbps_reference_no if bbps_info else None,
                "bill_paid_for_fullname": bbps_info.bill_paid_for_fullname if bbps_info else None,
                "bbps_status": bbps_info.status if bbps_info else None,
                "corrs_account_no": bbps_info.corrs_account_no if bbps_info else None,
                "corrs_message": bbps_info.corrs_message if bbps_info else None,
                "bbps_transaction_date": bbps_info.transaction_date.isoformat() if bbps_info and bbps_info.transaction_date else None,
                
                # Calculated Fields
                "lcr_money_applied": lcr_money_applied,
                "lcr_reward_applied": lcr_reward_applied,
                "net_service_value": net_service_value,
                "total_lcr_distributed": lcr_money_applied + lcr_reward_applied
            }
            
            result.append(record)
        
        print(f"✅ Returning {len(result)} consolidated transaction records")
        
        return {
            "success": True,
            "transaction_records": result,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": (total_records + page_size - 1) // page_size
            },
            "summary": {
                "total_service_amount": sum(r["service_amount"] for r in result),
                "total_lcr_money": sum(r["lcr_money_applied"] for r in result),
                "total_lcr_rewards": sum(r["lcr_reward_applied"] for r in result),
                "total_net_value": sum(r["net_service_value"] for r in result)
            }
        }
        
    except Exception as e:
        print(f"❌ Error in get_transaction_record: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

 