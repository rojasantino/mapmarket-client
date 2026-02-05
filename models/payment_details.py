from datetime import datetime
from db import db

class PaymentDetail(db.Model):
    __tablename__ = 'payment_details'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) 
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    payment_method = db.Column(db.String(50))  # 'razorpay', 'stripe', 'qr_code', 'cod'
    payment_mode = db.Column(db.String(50))  # 'card', 'upi', 'netbanking', 'wallet'
    
    # Legacy fields
    upi_id = db.Column(db.String(100))
    cardholder_name = db.Column(db.String(100))
    masked_card_number = db.Column(db.String(20))
    
    # Payment Gateway Integration
    gateway_name = db.Column(db.String(50))  # 'razorpay', 'stripe', 'qr_payment'
    gateway_response = db.Column(db.JSON)
    
    # Razorpay Fields
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)
    
    # Stripe Fields
    stripe_payment_intent_id = db.Column(db.String(100), nullable=True)
    stripe_charge_id = db.Column(db.String(100), nullable=True)
    
    # QR Payment Reference
    qr_payment_id = db.Column(db.Integer, db.ForeignKey('qr_payments.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_verified_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "payment_method": self.payment_method,
            "payment_mode": self.payment_mode,
            "upi_id": self.upi_id,
            "cardholder_name": self.cardholder_name,
            "masked_card_number": self.masked_card_number,
            "gateway_name": self.gateway_name,
            "gateway_response": self.gateway_response,
            "razorpay_order_id": self.razorpay_order_id,
            "razorpay_payment_id": self.razorpay_payment_id,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "qr_payment_id": self.qr_payment_id,
            "created_at": self.created_at.isoformat(),
            "payment_verified_at": self.payment_verified_at.isoformat() if self.payment_verified_at else None
        }
