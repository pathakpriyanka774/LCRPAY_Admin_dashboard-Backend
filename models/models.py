# models_postgres_sqlalchemy.py

from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
import pytz

from sqlalchemy import (Column, Integer, String, Boolean, DateTime, DECIMAL,
                        ForeignKey, Float, Text, UniqueConstraint, Index)
from sqlalchemy.orm import relationship

from core.base import Base, get_ist_time
from sqlalchemy import select, func
from decimal import Decimal
# Timezone setup
IST = pytz.timezone("Asia/Kolkata")


# ============================= USERS =============================
class User(Base):
    __tablename__ = "users"

    UserID = Column(Integer, primary_key=True)
    fullname = Column(String(255))
    MobileNumber = Column(String(15), nullable=False, unique=True)
    Email = Column(String(255))
    PasswordHash = Column(Text)
    LoginPIN = Column(String(100))
    TransactionPIN = Column(String(100))
    IsKYCCompleted = Column(Boolean, default=False)
    introducer_id = Column(String(255), ForeignKey("users.member_id"))
    member_id = Column(String(255), unique=True)
    RewardWalletBalance = Column(DECIMAL(10, 5), default=Decimal("0.00"))
    INRWalletBalance = Column(DECIMAL(10, 5), default=Decimal("0.00"))
    DeviceVerified = Column(Boolean, default=False)
    CreatedAt = Column(DateTime(timezone=True), default=get_ist_time)
    UpdatedAt = Column(DateTime(timezone=True))
    DeletedAt = Column(DateTime(timezone=True))
    IsDeleted = Column(Boolean, default=False)
    fingerPrintStatus = Column(Integer)
    activation_status = Column(Boolean, default=False)
    aadhar_verification_status = Column(Boolean, default=False)
    pan_verification_status = Column(Boolean, default=False)
    email_verification_status = Column(Boolean, default=False)
    prime_status = Column(Boolean, default=False)
    prime_activation_date = Column(DateTime(timezone=True))
    total_packages = Column(DECIMAL(10, 5), default=Decimal("0.00"))

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    upi_accounts = relationship("UserUPI", back_populates="user")
    transactions = relationship("Transactions", back_populates="user")
    memberships = relationship("Memberships", back_populates="user")
    payment_settings = relationship("PaymentSettings",
                                    back_populates="user",
                                    uselist=False)
    aadhar_user = relationship("Aadhar_User",
                               back_populates="user",
                               uselist=False)
    pan_verification = relationship("PanVerification",
                                    back_populates="user",
                                    uselist=False)
    wallet_transactions = relationship("Wallet", back_populates="user")
    offlineKYC = relationship("OfflineKYC",
                              back_populates="user",
                              uselist=False)
    fingerprint = relationship("FingerPrint",
                               back_populates="user",
                               uselist=False)

    introducer = relationship(
        "User",
        back_populates="referred_users",
        remote_side=[member_id],
        foreign_keys=[introducer_id],
    )
    referred_users = relationship(
        "User",
        back_populates="introducer",
        foreign_keys=[introducer_id],
    )

    direct_incomes_received = relationship(
        "DirectIncome",
        back_populates="receiver",
        foreign_keys="DirectIncome.receiver_member",
    )
    direct_incomes_activated = relationship(
        "DirectIncome",
        back_populates="prime_activator",
        foreign_keys="DirectIncome.prime_activated_by_member",
    )

    level_incomes_received = relationship(
        "LevelIncome",
        back_populates="level_receiver",
        foreign_keys="LevelIncome.receiver_member",
    )
    level_incomes_activated = relationship(
        "LevelIncome",
        back_populates="level_prime_activator",
        foreign_keys="LevelIncome.prime_activated_by_member",
    )

    prime_activations_received = relationship(
        "PrimeActivations",
        back_populates="receiver_member",
        foreign_keys="PrimeActivations.member",
    )
    prime_incomes_activated = relationship(
        "PrimeActivations",
        back_populates="prime_activator",
        foreign_keys="PrimeActivations.prime_initiated_by",
    )

    sent_transactions = relationship(
        "P2PTransaction",
        back_populates="sender",
        foreign_keys="P2PTransaction.transaction_from",
    )
    received_transactions = relationship(
        "P2PTransaction",
        back_populates="receiver",
        foreign_keys="P2PTransaction.transaction_to",
    )

    async def get_wallet_balance(self, session) -> Decimal:
        stmt = select(func.sum(Wallet.transaction_amount)) \
            .where(Wallet.transaction_by == self.UserID,
                Wallet.transaction_type == "credit",
                Wallet.status == "success")
        credit = (await session.execute(stmt)).scalar() or Decimal("0")

        stmt = select(func.sum(Wallet.transaction_amount)) \
            .where(Wallet.transaction_by == self.UserID,
                Wallet.transaction_type == "debit",
                Wallet.status == "success")
        debit = (await session.execute(stmt)).scalar() or Decimal("0")

        return credit - debit


# ============================= INCOME TABLES =============================
class IncomeDistribution(Base):
    __tablename__ = "income_distributions"

    id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False)
    reward = Column(DECIMAL(10, 5))
    package_amount = Column(DECIMAL(10, 5))
    set_date = Column(DateTime(timezone=True), default=get_ist_time)

    async def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class DirectIncome(Base):
    __tablename__ = "direct_income"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    prime_activated_by_member = Column(String(255),
                                       ForeignKey("users.member_id"),
                                       nullable=False)
    amount = Column(DECIMAL(10, 5))
    package_amount = Column(DECIMAL(10, 5))
    reference_id = Column(String(255))
    received_date = Column(DateTime(timezone=True), default=get_ist_time)

    receiver = relationship("User",
                            back_populates="direct_incomes_received",
                            foreign_keys=[receiver_member])
    prime_activator = relationship("User",
                                   back_populates="direct_incomes_activated",
                                   foreign_keys=[prime_activated_by_member])


class LevelIncome(Base):
    __tablename__ = "level_income"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    prime_activated_by_member = Column(String(255),
                                       ForeignKey("users.member_id"),
                                       nullable=False)
    level = Column(Integer)
    amount = Column(DECIMAL(10, 5))
    package_amount = Column(DECIMAL(10, 5))
    reference_id = Column(String(255))
    received_date = Column(DateTime(timezone=True), default=get_ist_time)

    level_receiver = relationship("User",
                                  back_populates="level_incomes_received",
                                  foreign_keys=[receiver_member])
    level_prime_activator = relationship(
        "User",
        back_populates="level_incomes_activated",
        foreign_keys=[prime_activated_by_member])


class MagicIncome(Base):
    __tablename__ = "magic_income"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    level = Column(Integer)
    amount = Column(DECIMAL(10, 5))
    package_amount = Column(DECIMAL(10, 5))
    received_date = Column(DateTime(timezone=True), default=get_ist_time)


class RoyaltyIncome(Base):
    __tablename__ = "royalty_income"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    total_members = Column(Integer)
    total_income_distribution = Column(DECIMAL(10, 5))
    amount = Column(DECIMAL(10, 5))
    type = Column(String(255))
    received_date = Column(DateTime(timezone=True), default=get_ist_time)


class PrimeActivations(Base):
    __tablename__ = "prime_activations"

    id = Column(Integer, primary_key=True)
    member = Column(String(255), ForeignKey("users.member_id"), nullable=False)
    prime_initiated_by = Column(String(255),
                                ForeignKey("users.member_id"),
                                nullable=False)
    reference_id = Column(String(255))
    package_amount = Column(DECIMAL(10, 5))
    activation_date = Column(DateTime(timezone=True), default=get_ist_time)

    receiver_member = relationship("User",
                                   back_populates="prime_activations_received",
                                   foreign_keys=[member])
    prime_activator = relationship("User",
                                   back_populates="prime_incomes_activated",
                                   foreign_keys=[prime_initiated_by])


# ============================= PROFILE / KYC =============================
# ============================= PROFILE / KYC =============================
class UserProfile(Base):
    __tablename__ = "userprofile"

    ProfileID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey("users.UserID"), nullable=False)
    FullName = Column(String(255))
    AadhaarNumber = Column(String(12))
    PANNumber = Column(String(10))
    UploadedDocuments = Column(Text)
    EmailVerified = Column(Boolean, default=False)
    KYCLevel = Column(Integer, default=0)
    TransferLimit = Column(Float)
    CreatedAt = Column(DateTime(timezone=True), default=get_ist_time)
    DeletedAt = Column(DateTime(timezone=True))
    IsDeleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile")


class UserUPI(Base):
    __tablename__ = "userupi"

    UPIID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey("users.UserID"))
    UPIAddress = Column(String(255))
    IsPrimary = Column(Boolean, default=False)
    CreatedAt = Column(DateTime(timezone=True), default=get_ist_time)
    DeletedAt = Column(DateTime(timezone=True))
    IsDeleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="upi_accounts")


class Transactions(Base):
    __tablename__ = "transactions"

    TransactionID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey("users.UserID"))
    TransactionType = Column(String(50))
    Amount = Column(DECIMAL(10, 5))
    Status = Column(String(50))
    TransactionPIN = Column(String(10))
    CreatedAt = Column(DateTime(timezone=True), default=get_ist_time)
    DeletedAt = Column(DateTime(timezone=True))
    IsDeleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="transactions")


class Memberships(Base):
    __tablename__ = "memberships"

    MembershipID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey("users.UserID"))
    Plan = Column(String(255))
    StartDate = Column(DateTime(timezone=True), default=get_ist_time)
    EndDate = Column(DateTime(timezone=True))
    Status = Column(String(50))
    CreatedAt = Column(DateTime(timezone=True), default=get_ist_time)
    DeletedAt = Column(DateTime(timezone=True))
    IsDeleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="memberships")


class Coupons(Base):
    __tablename__ = "coupons"

    CouponID = Column(Integer, primary_key=True)
    Code = Column(String(50), unique=True)
    DiscountPercentage = Column(Integer)
    MaxDiscount = Column(DECIMAL(10, 5))
    ValidFrom = Column(DateTime(timezone=True), default=get_ist_time)
    ValidTo = Column(DateTime(timezone=True), default=get_ist_time)
    IsRedeemable = Column(Boolean, default=True)


class Vouchers(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    prime_activated_by_member = Column(String(255),
                                       ForeignKey("users.member_id"))
    amount = Column(DECIMAL(10, 5))
    receivedDate = Column(DateTime(timezone=True), default=get_ist_time)
    redeemedDate = Column(DateTime(timezone=True))
    IsRedeemable = Column(Boolean, default=False)
    IsScratched = Column(Boolean, default=False)
    scratchDate = Column(DateTime(timezone=True))
    reference_id = Column(String(255))


class PaymentSettings(Base):
    __tablename__ = "payment_settings"

    SettingID = Column(Integer, primary_key=True)
    UserID = Column(Integer, ForeignKey("users.UserID"))
    AllowPayment = Column(Boolean, default=True)
    AllowWithdrawal = Column(Boolean, default=True)
    ModifiedBy = Column(Integer)
    ModifiedAt = Column(DateTime(timezone=True), default=get_ist_time)

    user = relationship("User", back_populates="payment_settings")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, nullable=False, index=True)
    receiver_id = Column(Integer, nullable=False, index=True)
    content = Column(String(5000), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=get_ist_time)


class Aadhar_User(Base):
    __tablename__ = "aadhar_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.UserID"), unique=True)
    name = Column(String(255))
    dateOfBirth = Column(DateTime)
    email = Column(String(255))
    gender = Column(String(10))
    generatedAt = Column(DateTime(timezone=True), default=get_ist_time)
    maskedNumber = Column(String(20))
    aadharNumber = Column(String(20))
    phone = Column(String(15))
    photo = Column(Text)
    address_id = Column(Integer, ForeignKey("user_aadhar_address.id"))

    user = relationship("User", back_populates="aadhar_user")
    address = relationship("User_Aadhar_Address", back_populates="aadhar_user")


class User_Aadhar_Address(Base):
    __tablename__ = "user_aadhar_address"

    id = Column(Integer, primary_key=True)
    careOf = Column(String(255))
    country = Column(String(255))
    district = Column(String(255))
    house = Column(String(255))
    landmark = Column(String(255))
    locality = Column(String(255))
    pin = Column(String(10))
    postOffice = Column(String(255))
    state = Column(String(255))
    street = Column(String(255))
    subDistrict = Column(String(255))
    vtc = Column(String(255))

    aadhar_user = relationship("Aadhar_User", back_populates="address")


class PanVerification(Base):
    __tablename__ = "pan_verification"

    user_id = Column(Integer, ForeignKey("users.UserID"), primary_key=True)
    pan_number = Column(String(20))
    pan_holder_name = Column(String(255))
    status = Column(String(50))
    category = Column(String(50))
    date_of_issue = Column(DateTime(timezone=True), default=get_ist_time)

    user = relationship("User", back_populates="pan_verification")


class OTPStore(Base):
    __tablename__ = "otp_store"

    id = Column(Integer, primary_key=True)
    MobileNumber = Column(String(15), nullable=False)
    otp = Column(String(255), nullable=False)
    expiry_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=get_ist_time)


# ============================= WALLET & P2P =============================
class Wallet(Base):
    __tablename__ = "wallet"

    id = Column(Integer, primary_key=True)
    transaction_by = Column(Integer, ForeignKey("users.UserID"))
    reference_id = Column(String(255), nullable=False)
    transaction_amount = Column(DECIMAL(10, 5), default=Decimal("0.00000"))
    transaction_type = Column(String(50))
    purpose = Column(String(255))
    remark = Column(String(255), default="")
    transaction_date = Column(DateTime(timezone=True), default=get_ist_time)
    transaction_mode = Column(String(50), default="online")
    utr_no = Column(String(255), unique=True)
    status = Column(String(50), default="pending")
    payment_screenshot = Column(String(500))

    user = relationship("User", back_populates="wallet_transactions")


class P2PTransaction(Base):
    __tablename__ = "p2p_transaction"

    id = Column(Integer, primary_key=True)
    transaction_from = Column(Integer, ForeignKey("users.UserID"))
    transaction_to = Column(Integer, ForeignKey("users.UserID"))
    reference_id = Column(String(255), nullable=False, unique=True)
    transaction_amount = Column(DECIMAL(10, 5))
    transaction_type = Column(String(10))
    transaction_date = Column(DateTime(timezone=True), default=get_ist_time)
    status = Column(String(15), default="pending")

    sender = relationship(
        "User",
        back_populates="sent_transactions",
        foreign_keys=[transaction_from],
    )
    receiver = relationship(
        "User",
        back_populates="received_transactions",
        foreign_keys=[transaction_to],
    )


# ============================= BANKING / CATALOG =============================
class AllBanksList(Base):
    __tablename__ = "bank_list"

    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, nullable=False)
    bank_name = Column(String(255), nullable=False)
    master_ifsc = Column(String(255), nullable=False)
    bank_code = Column(String(255), nullable=False)


class UserAddedBankDetails(Base):
    __tablename__ = "user_added_bank_details"

    id = Column(Integer, primary_key=True)
    uploaded_by = Column(String(255),
                         ForeignKey("users.member_id"),
                         nullable=False)
    bankACHolder = Column(String(255))
    bankACHolderPhoneNumber = Column(String(15))
    bankName = Column(String(255))
    bankIFSC = Column(String(255))
    bankACNumber = Column(String(50))
    bank_code = Column(String(20))
    bankAddedDate = Column(DateTime(timezone=True), default=get_ist_time)
    is_phone_verified = Column(Boolean, default=False)
    type = Column(String(20))
    beneficiary_id = Column(String(20))
    is_kyc_verfied = Column(Boolean, default=False)
    bankID = Column(String(20))

    # Optional relationship to the User via member_id (non-PK target)
    uploader = relationship(
        "User",
        primaryjoin="User.member_id==UserAddedBankDetails.uploaded_by",
        foreign_keys=[uploaded_by],
        viewonly=True,
    )


class NewOperator(Base):
    __tablename__ = "operators"

    OperatorID = Column(Integer, primary_key=True, index=True)
    OperatorName = Column(String(255), nullable=False, unique=True)
    OperatorCode = Column(Integer, nullable=False, unique=True)


class AllCircle(Base):
    __tablename__ = "circles"

    CircleID = Column(Integer, primary_key=True, index=True)
    CircleName = Column(String(255), nullable=False, unique=True)


# ============================= WITHDRAWALS =============================
class WithdrawalHistory(Base):
    __tablename__ = "withdrawal_history"

    id = Column(Integer, primary_key=True)
    transaction_by = Column(Integer, ForeignKey("users.UserID"))
    reference_id = Column(String(255), nullable=False)
    utr = Column(String(255), nullable=False)
    withdraw_amount = Column(DECIMAL(10, 5))
    trasferred_amount = Column(DECIMAL(10, 5))
    tds = Column(DECIMAL(10, 5))
    taxs_and_charges = Column(DECIMAL(10, 5))
    transaction_type = Column(String(10))
    remark = Column(String(255), default="")
    transaction_date = Column(DateTime(timezone=True), default=get_ist_time)
    transaction_mode = Column(String(10), default="online")
    transactionID = Column(String(255), unique=True)
    status = Column(String(15), default="pending")


# ============================= RECHARGE / INCENTIVES =============================
class RechargeIncentivesLevelWise(Base):
    __tablename__ = "recharge_incentives_new"

    id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False)
    mobile_recharge_incentive = Column(DECIMAL(10, 5),
                                       default=Decimal("0.00000"))
    d2h_recharge_incentive = Column(DECIMAL(10, 5), default=Decimal("0.00000"))
    bbps_all_services_incentive = Column(DECIMAL(10, 5),
                                         default=Decimal("0.00000"))
    isPrime = Column(Boolean, default=False)


class RechargeIncentivesIncomeDistribution(Base):
    __tablename__ = "recharge_incentives_income_distribution_new"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    recharge_by_member = Column(String(255),
                                ForeignKey("users.member_id"),
                                nullable=False)
    level = Column(Integer, nullable=False)
    amount = Column(DECIMAL(10, 5))
    recharge_amount = Column(DECIMAL(10, 5))
    recharge_percent = Column(DECIMAL(10, 5))
    reference_id = Column(String(255))
    service_used = Column(String(255))
    received_date = Column(DateTime(timezone=True), default=get_ist_time)

    receiver_user = relationship(
        "User",
        primaryjoin=
        "User.member_id==RechargeIncentivesIncomeDistribution.receiver_member",
        foreign_keys=[receiver_member],
        viewonly=True,
    )
    recharged_by_user = relationship(
        "User",
        primaryjoin=
        "User.member_id==RechargeIncentivesIncomeDistribution.recharge_by_member",
        foreign_keys=[recharge_by_member],
        viewonly=True,
    )


class RechargeCoinDistributions(Base):
    __tablename__ = "recharge_coin_distributions"

    id = Column(Integer, primary_key=True)
    receiver_member = Column(String(255),
                             ForeignKey("users.member_id"),
                             nullable=False)
    amount = Column(DECIMAL(10, 5))
    recharge_amount = Column(DECIMAL(10, 5))
    reference_id = Column(String(255))
    service_used = Column(String(255))
    received_date = Column(DateTime(timezone=True), default=get_ist_time)

    receiver_user = relationship(
        "User",
        primaryjoin="User.member_id==RechargeCoinDistributions.receiver_member",
        foreign_keys=[receiver_member],
        viewonly=True,
    )


# ============================= BILLS / BBPS =============================
class BillTransactions(Base):
    __tablename__ = "bbps_bill_payment_transactions"

    id = Column(Integer, primary_key=True)
    payee_member = Column(String(255),
                          ForeignKey("users.member_id"),
                          nullable=False)
    amount = Column(DECIMAL(10, 5))
    reference_id = Column(String(255))
    bbps_service_name = Column(String(255))
    bill_paymet_reference_no = Column(String(255))
    bbps_reference_no = Column(String(255))
    bill_paid_for_fullname = Column(String(255))
    transaction_date = Column(DateTime(timezone=True), default=get_ist_time)
    status = Column(Boolean, default=False)
    corrs_account_no = Column(String(5000))
    corrs_message = Column(String(255))

    payee_user = relationship(
        "User",
        primaryjoin="User.member_id==BillTransactions.payee_member",
        foreign_keys=[payee_member],
        viewonly=True,
    )


class GenerateReferenceNo(Base):
    __tablename__ = "generated_refernce_no"

    id = Column(Integer, primary_key=True)
    reference_no = Column(String(50), nullable=False)


# ============================= QR / UPI GATEWAY =============================
class AddToWalletQr(Base):
    __tablename__ = "add_to_wallet_qr"

    id = Column(Integer, primary_key=True)
    client_txn_id = Column(String(255), nullable=False)
    amount = Column(DECIMAL(10, 5))
    member_id = Column(String(255),
                       ForeignKey("users.member_id"),
                       nullable=False)
    status = Column(Boolean, default=False)
    createdAt = Column(DateTime(timezone=True), default=get_ist_time)

    member_user = relationship(
        "User",
        primaryjoin="User.member_id==AddToWalletQr.member_id",
        foreign_keys=[member_id],
        viewonly=True,
    )


class UpiGatewayTransaction(Base):
    __tablename__ = "upi_gateway_transactions_new"

    id = Column(Integer, primary_key=True)
    amount = Column(DECIMAL(10, 5))
    client_txn_id = Column(String(255), index=True, nullable=False)
    customer_email = Column(String(255))
    customer_mobile = Column(String(20))
    customer_name = Column(String(255))
    customer_vpa = Column(String(255))  # UPI ID if payment is successful
    p_info = Column(String(255))
    redirect_url = Column(String(255))
    remark = Column(String(255))
    status = Column(String(20))  # success / failure
    txn_at = Column(DateTime(timezone=True))
    udf1 = Column(String(255))
    udf2 = Column(String(255))
    udf3 = Column(String(255))
    upi_txn_id = Column(String(255))  # merchant app txn id or UTR number
    created_at = Column(DateTime(timezone=True), nullable=False)


# ============================= OFFLINE KYC / PAN OFFLINE =============================
class PanOfflineKYC(Base):
    __tablename__ = "pan_offline_kyc"

    id = Column(Integer, primary_key=True, index=True)
    pan_front = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    pan_name = Column(String(255), nullable=False)
    pan_no = Column(String(50), nullable=False)
    offline_kyc_id = Column(Integer,
                            ForeignKey("offline_kyc.id"),
                            nullable=False)

    offline_kyc = relationship("OfflineKYC", back_populates="pan_offline_kyc")


class OfflineKYC(Base):
    __tablename__ = "offline_kyc"

    id = Column(Integer, primary_key=True, index=True)
    aadhar_front_filename = Column(Text, nullable=False)
    aadhar_back_filename = Column(Text, nullable=False)
    name = Column(String(255), nullable=False)
    dob = Column(
        DateTime, nullable=False
    )  # original used date; keep as DateTime if you want tz-naive dates
    aadhar_no = Column(String(50), nullable=False)
    district = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    user_id = Column(Integer, ForeignKey("users.UserID"), nullable=False)

    user = relationship("User", back_populates="offlineKYC")
    pan_offline_kyc = relationship("PanOfflineKYC",
                                   back_populates="offline_kyc",
                                   uselist=False)


# ============================= MISC / SUPPORT =============================
class PackageTab(Base):
    __tablename__ = "package_tab"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=get_ist_time)
    amount = Column(Float)


class FingerPrint(Base):
    __tablename__ = "fingerprint"

    id = Column(Integer, primary_key=True)
    status = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.UserID"), nullable=False)

    user = relationship("User", back_populates="fingerprint")


class Operator(Base):
    __tablename__ = "operator"

    id = Column(Integer, primary_key=True)
    operator_name = Column(String(255))
    operator_id = Column(String(255))
    service_type = Column(String(255))
    status = Column(Integer)
    biller_status = Column(String(255))
    bill_fetch = Column(String(255))
    supportValidation = Column(String(255), default="None")
    bbps_enabled = Column(String(255))
    message = Column(String(255))
    description = Column(String(255))
    amount_minimum = Column(Float)
    amount_maximum = Column(Float)


class Circlecode(Base):
    __tablename__ = "circlecode"

    id = Column(Integer, primary_key=True)
    circle_name = Column(String(255))
    circle_code = Column(String(255))


class Emailotp(Base):
    __tablename__ = "emailotp"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    otp = Column(String(6), nullable=False)
    expiry_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=get_ist_time)


class LCRPackages(Base):
    __tablename__ = "lcr_packages"

    srno = Column(Integer, primary_key=True)
    amount = Column(DECIMAL(10, 5), default=Decimal("0.00000"))
    package_name = Column(String(50))


class LcrMoneyDistributionAmount(Base):
    __tablename__ = "lcr_money_distribution_amount"

    srno = Column(Integer, primary_key=True)
    amount = Column(DECIMAL(10, 5), default=Decimal("0.00000"))
    purpose = Column(String(255))
    set_date = Column(DateTime(timezone=True), default=get_ist_time)


class LcrRewards(Base):
    __tablename__ = "lcr_rewards"

    srno = Column(Integer, primary_key=True)
    amount = Column(DECIMAL(10, 5), default=Decimal("0.00000"))
    reference_id = Column(String(255))
    transactiontype = Column(String(255))
    received_by = Column(String(255))
    received_from = Column(String(255))
    transactiondate = Column(DateTime(timezone=True))
    status = Column(Integer, index=True)
    received_for = Column(String(255))
    purpose = Column(String(50))
    remark = Column(String(255))
    validity = Column(DateTime(timezone=True))
    other = Column(String(255))


class LcrMoney(Base):
    __tablename__ = "lcrmoney"

    srno = Column(Integer, primary_key=True)
    amount = Column(DECIMAL(10, 5), default=Decimal("0.00000"))
    transactiontype = Column(String(255))
    reference_id = Column(String(255))
    received_by = Column(String(255))
    received_from = Column(String(255))
    transactiondate = Column(DateTime(timezone=True))
    status = Column(Integer, index=True)
    received_for = Column(String(255))
    purpose = Column(String(50))
    remark = Column(String(255))
    validity = Column(DateTime(timezone=True))
    other = Column(String(255))
