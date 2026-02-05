# utils/otp_generator.py
import random
import string
from datetime import datetime, timedelta
from models.email_otp import EmailOTP
from db import db

class OTPGenerator:
    """Utility class for OTP generation and validation"""
    
    @staticmethod
    def generate_numeric_otp(length=6):
        """Generate a numeric OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def generate_alphanumeric_otp(length=6):
        """Generate an alphanumeric OTP"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    @staticmethod
    def create_email_otp(email, purpose="verification", expiry_minutes=10):
        """Create and save an email OTP"""
        # Invalidate any existing pending OTPs for this email and purpose
        existing_otps = EmailOTP.query.filter_by(
            email=email,
            purpose=purpose,
            verified=False
        ).all()
        
        for otp in existing_otps:
            db.session.delete(otp)
        
        # Create new OTP
        new_otp = EmailOTP(email=email, purpose=purpose, expiry_minutes=expiry_minutes)
        db.session.add(new_otp)
        db.session.commit()
        
        return new_otp
    
    @staticmethod
    def verify_email_otp(email, otp_code, purpose="verification"):
        """Verify an email OTP"""
        otp_record = EmailOTP.query.filter_by(
            email=email,
            purpose=purpose,
            verified=False
        ).order_by(EmailOTP.created_at.desc()).first()
        
        if not otp_record:
            return False, "No OTP found for this email"
        
        success, message = otp_record.verify(otp_code)
        
        if success:
            db.session.commit()
        
        return success, message
    
    @staticmethod
    def check_rate_limit(email, purpose, max_requests=5, time_window_minutes=60):
        """Check if user has exceeded OTP request rate limit"""
        time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        recent_requests = EmailOTP.query.filter(
            EmailOTP.email == email,
            EmailOTP.purpose == purpose,
            EmailOTP.created_at >= time_threshold
        ).count()
        
        if recent_requests >= max_requests:
            return False, f"Too many OTP requests. Please try again later."
        
        return True, "Rate limit OK"
    
    @staticmethod
    def cleanup_expired_otps():
        """Clean up expired OTPs (can be run as a background task)"""
        expired_otps = EmailOTP.query.filter(
            EmailOTP.expires_at < datetime.utcnow(),
            EmailOTP.verified == False
        ).all()
        
        count = len(expired_otps)
        for otp in expired_otps:
            db.session.delete(otp)
        
        db.session.commit()
        return count
