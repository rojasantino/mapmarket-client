from datetime import datetime
from db import db

class PaymentDetail(db.Model):
    __tablename__ = 'payment_details'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) 
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_method = db.Column(db.String(50))
    payment_mode = db.Column(db.String(50))
    upi_id = db.Column(db.String(100))
    cardholder_name = db.Column(db.String(100))
    masked_card_number = db.Column(db.String(20))
    gateway_name = db.Column(db.String(50))
    gateway_response = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            "created_at": self.created_at.isoformat()
        }
