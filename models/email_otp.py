# models/email_otp.py
from datetime import datetime, timedelta
from db import db
import random
import string

class EmailOTP(db.Model):
    __tablename__ = 'email_otp'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)  # 'registration', 'order_confirmation', 'password_reset'
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attempts = db.Column(db.Integer, default=0)  # Track verification attempts

    def __init__(self, email, purpose, expiry_minutes=10):
        self.email = email
        self.purpose = purpose
        self.otp_code = self.generate_otp()
        self.expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

    @staticmethod
    def generate_otp(length=6):
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=length))

    def is_expired(self):
        """Check if OTP has expired"""
        return datetime.utcnow() > self.expires_at

    def verify(self, otp_code):
        """Verify the OTP code"""
        self.attempts += 1
        
        if self.is_expired():
            return False, "OTP has expired"
        
        if self.verified:
            return False, "OTP already used"
        
        if self.attempts > 5:
            return False, "Too many attempts"
        
        if self.otp_code != otp_code:
            return False, "Invalid OTP"
        
        self.verified = True
        self.verified_at = datetime.utcnow()
        return True, "OTP verified successfully"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "purpose": self.purpose,
            "expires_at": self.expires_at.isoformat(),
            "verified": self.verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat()
        }
