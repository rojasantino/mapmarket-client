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

    order_status = db.Column(db.String(20), default='placed')

    cancel_reason = db.Column(db.String(255))
    cancelled_at = db.Column(db.DateTime)

    order_date = db.Column(db.DateTime, default=datetime.utcnow)

    billing_info = db.relationship("BillingInfo", backref="orders", lazy=True)
    payment_details = db.relationship("PaymentDetail", backref="order", lazy=True)

    def to_dict(self):
        return {
            # ✅ Expose PUBLIC ID
            "order_id": self.order_number,
            "id": self.id,
            # ⚠ Internal ID (optional – remove if not needed)
            # "internal_id": self.id,

            "user_id": self.user_id,
            "billing_info_id": self.billing_info_id,
            "items": self.items,
            "total_amount": float(self.total_amount),
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "payment_reference": self.payment_reference,
            "order_status": self.order_status,
            "order_date": self.order_date.isoformat(),
            "cancel_reason": self.cancel_reason,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "billing_info": self.billing_info.to_dict() if self.billing_info else None
        }
