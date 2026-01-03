from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Numeric, or_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from models.models import User, Transactions, DirectIncome, LevelIncome, LcrMoney, LcrRewards,BillTransactions
from models.payment_gateway import Payment_Gateway
from models.service_request import Service_Request



class DashboardService:

    @staticmethod
    def get_dashboard_stats(db: Session):
        try:
            # ============ USER STATS - NO JOINS ============
            # Total users - excluding deleted (STRICT NULL CHECK)
            total_users = db.query(User).filter(
                User.IsDeleted.is_(False) | User.IsDeleted.is_(None)
            ).count()

            # Debug print
            print(f"🔍 Total Users Query Result: {total_users}")

            # New signups today
            today = datetime.now().date()
            new_signups_today = db.query(User).filter(
                func.date(User.CreatedAt) == today,
                or_(User.IsDeleted == False, User.IsDeleted == None)
            ).count()

            # New signups in last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            new_signups_last_7_days = db.query(User).filter(
                User.CreatedAt >= seven_days_ago,
                or_(User.IsDeleted == False, User.IsDeleted == None)
            ).count()

            # KYC verified users
            kyc_verified_users = db.query(User).filter(
                User.IsKYCCompleted == True,
                or_(User.IsDeleted == False, User.IsDeleted == None)
            ).count()

            # KYC verification percentage
            kyc_verification_percentage = (
                (kyc_verified_users / total_users * 100) if total_users > 0 else 0
            )

            # Prime users
            prime_users = db.query(User).filter(
                User.prime_status == True,
                or_(User.IsDeleted == False, User.IsDeleted == None)
            ).count()

            # ============ INCOME STATS - COUNT FROM INCOME TABLES ============
            # ============ LCR MONEY & REWARDS - DIRECTLY FROM TABLES ============

            # Total LCR Money Distributed - DIRECT SUM from lcrmoney table
            total_lcr_money = db.query(
                func.coalesce(func.sum(LcrMoney.amount), 0)
            ).filter(
                LcrMoney.status == 1  # Active status only
            ).scalar() or 0
            total_lcr_money = float(total_lcr_money)

            # Total LCR Reward Distributed - DIRECT SUM from lcr_rewards table
            total_lcr_reward_distributed = db.query(
                func.coalesce(func.sum(LcrRewards.amount), 0)
            ).filter(
                LcrRewards.status == 1  # Active status only
            ).scalar() or 0
            total_lcr_reward_distributed = float(total_lcr_reward_distributed)

            # Count unique users who received direct income
            direct_income_users = db.query(func.count(func.distinct(DirectIncome.receiver_member))).scalar() or 0

            # Count unique users who received level income
            level_income_users = db.query(func.count(func.distinct(LevelIncome.receiver_member))).scalar() or 0

            # Total Distributor LCR Money = Users with any wallet balance
            total_distributor_lcr_money = db.query(User).filter(
                or_(User.INRWalletBalance > 0, User.RewardWalletBalance > 0),
                or_(User.IsDeleted == False, User.IsDeleted == None)
            ).count()

            # Total Distributor Prime Reward = Unique users from DirectIncome + LevelIncome
            total_prime_reward = direct_income_users + level_income_users

            # ============ PAYMENT GATEWAY STATS - NO JOINS, DIRECT COUNT ============
            # Mobile recharge count - ONLY from payment_gateway table, no joins
            total_mobile_recharge = db.query(func.count(Payment_Gateway.id)).filter(
                or_(
                    Payment_Gateway.purpose.ilike('%mobile%'),
                    Payment_Gateway.purpose.ilike('%recharge%')
                ),
                Payment_Gateway.status == 'SUCCESS'
            ).scalar() or 0

            # DTH recharge count - ONLY from payment_gateway table, no joins
            total_dth_recharge = db.query(func.count(Payment_Gateway.id)).filter(
                Payment_Gateway.purpose.ilike('%dth%'),
                Payment_Gateway.status == 'SUCCESS'
            ).scalar() or 0

            # Total Payment Requests - ALL payment gateway records
            total_payment_requests = db.query(func.count(Payment_Gateway.id)).scalar() or 0

            # Calculate verified accounts (KYC completed users)
            verified_accounts = kyc_verified_users

            print(f"📊 Dashboard Stats Debug (DIRECT CALCULATION):")
            print(f"   Total Users: {total_users}")
            print(f"   New Signups Today: {new_signups_today}")
            print(f"   New Signups Last 7 Days: {new_signups_last_7_days}")
            print(f"   KYC Verified: {kyc_verified_users}")
            print(f"   Prime Users: {prime_users}")
            print(f"   Total LCR Money (DIRECT SUM from lcrmoney table, status=1): {total_lcr_money}")
            print(f"   Total LCR Reward Distributed (DIRECT SUM from lcr_rewards table, status=1): {total_lcr_reward_distributed}")
            print(f"   Total Payment Requests: {total_payment_requests}")
            print(f"   Total Distributor LCR Money (users with any wallet balance): {total_distributor_lcr_money}")
            print(f"   Total Distributor Prime Reward (DirectIncome + LevelIncome users): {total_prime_reward}")
            print(f"   Mobile Recharge (payment_gateway count): {total_mobile_recharge}")
            print(f"   DTH Recharge (payment_gateway count): {total_dth_recharge}")

            return {
                "total_users": total_users,
                "new_signups_today": new_signups_today,
                "new_signups_last_7_days": new_signups_last_7_days,
                "kyc_verified_users": kyc_verified_users,
                "verified_accounts": verified_accounts,
                "kyc_verification_percentage": round(kyc_verification_percentage, 2),
                "prime_users": prime_users,
                "total_lcr_money": total_lcr_money,
                "total_lcr_reward_distributed": total_lcr_reward_distributed,
                "total_payment_requests": total_payment_requests,
                "total_distributor_lcr_money": total_distributor_lcr_money,
                "total_distributor_prime_reward": total_prime_reward,
                "total_mobile_recharge": total_mobile_recharge,
                "total_dth_recharge": total_dth_recharge
            }
        except Exception as e:
            print(f"❌ Error fetching dashboard stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                "total_users": 0,
                "new_signups_today": 0,
                "new_signups_last_7_days": 0,
                "kyc_verified_users": 0,
                "verified_accounts": 0,
                "kyc_verification_percentage": 0.0,
                "prime_users": 0,
                "total_lcr_money": 0.0,
                "total_lcr_reward_distributed": 0.0,
                "total_payment_requests": 0,
                "total_distributor_lcr_money": 0.0,
                "total_distributor_prime_reward": 0.0,
                "total_mobile_recharge": 0,
                "total_dth_recharge": 0
            }

    @staticmethod
    def get_recent_transactions(db: Session, limit: int = 50):
        transactions = db.query(Transactions).order_by(
            desc(Transactions.CreatedAt)).limit(limit).all()

        return [{
            "id": txn.TransactionID,
            "user": txn.UserName or "Unknown",
            "type": txn.TransactionType or "Recharge",
            "amount": float(txn.Amount) if txn.Amount else 0.0,
            "status": txn.Status,
            "date": txn.CreatedAt.strftime("%Y-%m-%d") if txn.CreatedAt else "",
            "time": txn.CreatedAt.strftime("%H:%M:%S") if txn.CreatedAt else ""
        } for txn in transactions]

    @staticmethod
    def get_live_transactions(db: Session, limit: int = 100):
        """Get latest live transactions for WebSocket streaming - REAL DATA ONLY"""
        result = []
        total_count = 0

        # Try Payment_Gateway table first with user join for real names
        try:
            # Get total count
            total_count = db.query(func.count(Payment_Gateway.id)).scalar() or 0

            pg_txns = db.query(
                Payment_Gateway,
                User.fullname,
                User.MobileNumber
            ).outerjoin(
                User, Payment_Gateway.member_id == User.UserID
            ).order_by(
                desc(Payment_Gateway.created_at)
            ).limit(limit).all()

            print(f"📊 Payment_Gateway transactions found: {len(pg_txns)} out of {total_count} total")

            for txn, user_fullname, user_mobile in pg_txns:
                # Use actual user fullname from User table if available
                display_name = user_fullname or txn.payer_name or user_mobile or f"User-{txn.member_id}"

                result.append({
                    "id": txn.client_txn_id or f"PG{txn.id}",
                    "TransactionID": txn.client_txn_id or f"PG{txn.id}",
                    "user": display_name,
                    "fullname": display_name,
                    "payer_name": display_name,
                    "service": txn.purpose or "Service",
                    "purpose": txn.purpose or "Service",
                    "amount": float(txn.amount) if txn.amount else 0.0,
                    "status": txn.status.capitalize() if txn.status else "Pending",
                    "location": "India",
                    "date": txn.created_at.strftime('%Y-%m-%d') if txn.created_at else "",
                    "time": txn.created_at.strftime('%H:%M:%S') if txn.created_at else ""
                })
        except Exception as e:
            print(f"Error fetching Payment_Gateway: {e}")

        # If no Payment_Gateway data, try Transactions table
        if not result:
            try:
                # Get total count
                total_count = db.query(func.count(Transactions.TransactionID)).scalar() or 0

                transactions = db.query(Transactions).join(
                    User, Transactions.UserID == User.UserID
                ).order_by(
                    desc(Transactions.CreatedAt)
                ).limit(limit).all()

                print(f"📊 Transactions table records found: {len(transactions)} out of {total_count} total")

                for txn in transactions:
                    result.append({
                        "id": str(txn.TransactionID),
                        "TransactionID": str(txn.TransactionID),
                        "user": txn.user.fullname if txn.user else "Unknown User",
                        "fullname": txn.user.fullname if txn.user else "Unknown User",
                        "service": txn.TransactionType or "Transaction",
                        "purpose": txn.TransactionType or "Transaction",
                        "amount": float(txn.Amount) if txn.Amount else 0.0,
                        "status": txn.Status.capitalize() if txn.Status else "Pending",
                        "location": "India",
                        "date": txn.CreatedAt.strftime('%Y-%m-%d') if txn.CreatedAt else "",
                        "time": txn.CreatedAt.strftime('%H:%M:%S') if txn.CreatedAt else ""
                    })
            except Exception as e:
                print(f"Error fetching Transactions: {e}")

        print(f"📊 Returning {len(result)} transactions out of {total_count} total")

        return {
            "transactions": result,
            "total_count": total_count,
            "showing_count": len(result)
        }

    @staticmethod
    def get_recent_users(db: Session, limit: int = 100):
        # Get verified and partially verified users only
        users = db.query(User).filter(
            or_(User.IsDeleted == False, User.IsDeleted == None),
            or_(
                # Fully verified (both aadhaar and pan)
                (User.aadhar_verification_status == True) & (User.pan_verification_status == True),
                # Partially verified (either aadhaar or pan)
                (User.aadhar_verification_status == True) & (User.pan_verification_status == False),
                (User.aadhar_verification_status == False) & (User.pan_verification_status == True)
            )
        ).order_by(desc(User.CreatedAt)).limit(limit).all()

        result = []
        for user in users:
            # Determine role based on user attributes
            role = "Retailer"
            if user.prime_status:
                role = "Distributor"

            result.append({
                "id": str(user.UserID),
                "name": user.fullname or "Unknown User",
                "email": user.Email or "",
                "mobile": user.MobileNumber or "",
                "role": role,
                "location": "India",
                "device": "Mobile" if user.DeviceVerified else "Desktop",
                "registered_at": user.CreatedAt.isoformat() if user.CreatedAt else datetime.now().isoformat()
            })

        print(f"📊 Recent Users (Verified/Partial): {len(result)} users")
        return result

    @staticmethod
    def get_chart_data(db: Session):
        last_7_days = [
            datetime.now().date() - timedelta(days=i)
            for i in range(6, -1, -1)
        ]

        daily_volume = []
        for day in last_7_days:
            # Get from Service_Request table (main source)
            sr_count = db.query(Service_Request).filter(
                func.date(Service_Request.created_at) == day,
                Service_Request.status.in_(['completed', 'paid', 'success'])
            ).count()

            sr_amount = db.query(
                func.coalesce(func.sum(Service_Request.amount), 0)
            ).filter(
                func.date(Service_Request.created_at) == day,
                Service_Request.status.in_(['completed', 'paid', 'success'])
            ).scalar() or 0

            # Also check Payment_Gateway
            pg_count = db.query(Payment_Gateway).filter(
                func.date(Payment_Gateway.created_at) == day,
                Payment_Gateway.status == 'SUCCESS'
            ).count()

            pg_amount = db.query(
                func.coalesce(func.sum(cast(Payment_Gateway.amount, Numeric)), 0)
            ).filter(
                func.date(Payment_Gateway.created_at) == day,
                Payment_Gateway.status == 'SUCCESS'
            ).scalar() or 0

            # Use whichever has more data
            total_count = max(sr_count, pg_count)
            total_amount = max(float(sr_amount), float(pg_amount))

            daily_volume.append({
                "name": day.strftime("%b %d"),
                "transactions": total_count,
                "amount": round(total_amount, 2)
            })

        # Service distribution from Service_Request (PRIMARY SOURCE)
        service_data = db.query(
            Service_Request.service_type,
            func.count(Service_Request.id).label('count')
        ).filter(
            Service_Request.service_type.isnot(None),
            Service_Request.status.in_(['completed', 'paid', 'success'])
        ).group_by(Service_Request.service_type).all()

        # Categorize services properly
        service_categories = {
            'Mobile Recharge': 0,
            'Prime Activation': 0,
            'DTH Service': 0,
            'BBPS Bill Payment': 0,
            'Other Services': 0
        }

        for service_type, count in service_data:
            service_lower = service_type.lower() if service_type else ""

            if 'mobile' in service_lower and 'recharge' in service_lower:
                service_categories['Mobile Recharge'] += count
            elif 'prime' in service_lower:
                service_categories['Prime Activation'] += count
            elif 'dth' in service_lower:
                service_categories['DTH Service'] += count
            elif 'bbps' in service_lower or 'bill' in service_lower:
                service_categories['BBPS Bill Payment'] += count
            else:
                service_categories['Other Services'] += count

        # Calculate total for percentage
        total_services = sum(service_categories.values())

        colors = {
            'Mobile Recharge': '#3b82f6',      # Blue
            'Prime Activation': '#10b981',     # Green
            'DTH Service': '#f59e0b',          # Orange
            'BBPS Bill Payment': '#ef4444',    # Red
            'Other Services': '#8b5cf6'        # Purple
        }

        service_distribution = []

        if total_services > 0:
            for service_name, count in service_categories.items():
                if count > 0:  # Only show services with transactions
                    percentage = (count / total_services) * 100
                    service_distribution.append({
                        "name": service_name,
                        "value": round(percentage, 1),
                        "color": colors[service_name]
                    })
        else:
            service_distribution = [{"name": "No Data", "value": 0, "color": "#9ca3af"}]

        print(f"📈 Chart Data Debug:")
        print(f"   Daily Volume Days: {len(daily_volume)}")
        print(f"   Daily Volume Data: {daily_volume}")
        print(f"   Service Categories: {service_categories}")
        print(f"   Service Distribution: {len(service_distribution)} services")
        print(f"   Service Distribution Data: {service_distribution}")

        return {
            "daily_volume": daily_volume,
            "service_distribution": service_distribution
        }