# models/order_timeline.py
from datetime import datetime
from db import db

class OrderTimeline(db.Model):
    __tablename__ = 'order_timeline'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(200), nullable=True)  # Current location for tracking
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_by = db.Column(db.String(100), nullable=True)  # User/System who made the update
    event_metadata = db.Column(db.JSON, nullable=True)  # Additional tracking data

    def __init__(self, order_id, status, description=None, location=None, updated_by=None, event_metadata=None):
        self.order_id = order_id
        self.status = status
        self.description = description
        self.location = location
        self.updated_by = updated_by
        self.event_metadata = event_metadata

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "status": self.status,
            "description": self.description,
            "location": self.location,
            "timestamp": self.timestamp.isoformat(),
            "updated_by": self.updated_by,
            "event_metadata": self.event_metadata
        }

    @staticmethod
    def create_timeline_entry(order_id, status, description=None, location=None, updated_by="system"):
        """Helper method to create a timeline entry"""
        entry = OrderTimeline(
            order_id=order_id,
            status=status,
            description=description,
            location=location,
            updated_by=updated_by
        )
        db.session.add(entry)
        return entry
