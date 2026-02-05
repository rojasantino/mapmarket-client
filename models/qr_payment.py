# models/qr_payment.py
from datetime import datetime, timedelta
from db import db
import uuid

class QRPayment(db.Model):
    __tablename__ = 'qr_payments'

    id = db.Column(db.Integer, primary_key=True)
    qr_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # UPI Details
    upi_id = db.Column(db.String(100), nullable=False)  # Merchant UPI ID
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    
    # QR Code Data
    qr_code_data = db.Column(db.Text, nullable=False)  # UPI payment string
    qr_code_image = db.Column(db.Text, nullable=True)  # Base64 encoded QR image
    
    # Payment Status
    status = db.Column(db.String(20), default='pending')  # pending, completed, expired, failed
    transaction_id = db.Column(db.String(100), nullable=True)  # UPI transaction ID
    transaction_ref = db.Column(db.String(100), nullable=True)  # Bank reference number
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    payment_metadata = db.Column(db.JSON, nullable=True)

    def __init__(self, order_id, upi_id, amount, expiry_minutes=15):
        self.qr_id = f"QR-{uuid.uuid4().hex[:12].upper()}"
        self.order_id = order_id
        self.upi_id = upi_id
        self.amount = amount
        self.expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        self.qr_code_data = self.generate_upi_string()

    def generate_upi_string(self):
        """Generate UPI payment string for QR code"""
        # UPI format: upi://pay?pa=<UPI_ID>&pn=<NAME>&am=<AMOUNT>&cu=<CURRENCY>&tn=<NOTE>
        upi_string = (
            f"upi://pay?"
            f"pa={self.upi_id}&"
            f"pn=MapMarket&"
            f"am={float(self.amount)}&"
            f"cu={self.currency}&"
            f"tn=Order Payment {self.qr_id}"
        )
        return upi_string

    def is_expired(self):
        """Check if QR payment has expired"""
        return datetime.utcnow() > self.expires_at

    def mark_completed(self, transaction_id, transaction_ref=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.transaction_id = transaction_id
        self.transaction_ref = transaction_ref
        self.verified_at = datetime.utcnow()

    def mark_expired(self):
        """Mark payment as expired"""
        if self.status == 'pending':
            self.status = 'expired'

    def to_dict(self, include_qr_data=True):
        data = {
            "id": self.id,
            "qr_id": self.qr_id,
            "order_id": self.order_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "transaction_ref": self.transaction_ref,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "is_expired": self.is_expired()
        }
        
        if include_qr_data:
            data["qr_code_data"] = self.qr_code_data
            data["qr_code_image"] = self.qr_code_image
        
        return data
