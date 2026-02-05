# models/orders.py
from datetime import datetime
import uuid
from db import db

class Order(db.Model):
    __tablename__ = 'orders'

    # INTERNAL ID (DO NOT EXPOSE)
    id = db.Column(db.Integer, primary_key=True)

    # PUBLIC ORDER ID (EXPOSE THIS)
    order_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: f"MAP-{uuid.uuid4().hex[:8].upper()}"
    )

    user_id = db.Column(db.Integer, nullable=False)
    billing_info_id = db.Column(
        db.Integer,
        db.ForeignKey('billing_info.id'),
        nullable=True
    )

    items = db.Column(db.JSON, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment_method = db.Column(db.String(50))
    payment_status = db.Column(db.String(20), default='pending')
    payment_reference = db.Column(db.String(100))

    # Order Status: placed, confirmed, processing, shipped, out_for_delivery, delivered, cancelled, returned
    order_status = db.Column(db.String(20), default='placed')

    # Delivery Tracking Fields
    delivery_partner = db.Column(db.String(100), nullable=True)  # e.g., "FedEx", "DHL", "Local Courier"
    tracking_number = db.Column(db.String(100), nullable=True, index=True)
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    delivery_otp = db.Column(db.String(4), nullable=True)  # 4-digit OTP for delivery confirmation
    
    # Timestamps
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    out_for_delivery_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    cancel_reason = db.Column(db.String(255))
    cancelled_at = db.Column(db.DateTime)

    billing_info = db.relationship("BillingInfo", backref="orders", lazy=True)
    payment_details = db.relationship("PaymentDetail", backref="order", lazy=True)
    timeline = db.relationship("OrderTimeline", backref="order", lazy=True, order_by="OrderTimeline.timestamp.desc()")

    def to_dict(self, include_timeline=False):
        data = {
            # ✅ Expose PUBLIC ID
            "order_id": self.order_number,
            "id": self.id,

            "user_id": self.user_id,
            "billing_info_id": self.billing_info_id,
            "items": self.items,
            "total_amount": float(self.total_amount),
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "payment_reference": self.payment_reference,
            "order_status": self.order_status,
            
            # Delivery Tracking
            "delivery_partner": self.delivery_partner,
            "tracking_number": self.tracking_number,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            
            # Timestamps
            "order_date": self.order_date.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "out_for_delivery_at": self.out_for_delivery_at.isoformat() if self.out_for_delivery_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            
            "cancel_reason": self.cancel_reason,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "billing_info": self.billing_info.to_dict() if self.billing_info else None
        }
        
        if include_timeline:
            data["timeline"] = [entry.to_dict() for entry in self.timeline]
        
        return data
