# routes/email_routes.py
from flask import request, jsonify, current_app as app
from auth import auth
from utils.email_service import EmailService
from utils.otp_generator import OTPGenerator
from db import db
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()

@app.route("/api/email/send-otp", methods=["POST"])
def send_otp():
    """Send OTP to email address"""
    try:
        data = request.get_json()
        email = data.get('email')
        purpose = data.get('purpose', 'verification')  # verification, order_confirmation, password_reset
        
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400
        
        # Check rate limit
        can_proceed, rate_message = OTPGenerator.check_rate_limit(email, purpose)
        if not can_proceed:
            return jsonify({"status": "error", "message": rate_message}), 429
        
        # Create OTP
        otp_record = OTPGenerator.create_email_otp(email, purpose)
        
        # Send email
        success, message = email_service.send_otp_email(email, otp_record.otp_code, purpose)
        
        if not success:
            logger.error(f"Failed to send OTP email: {message}")
            return jsonify({
                "status": "error",
                "message": "Failed to send OTP email. Please try again."
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "OTP sent successfully",
            "expires_in_minutes": 10,
            "otp_id": otp_record.id
        }), 200
        
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/api/email/verify-otp", methods=["POST"])
def verify_otp():
    """Verify OTP code"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp_code = data.get('otp_code')
        purpose = data.get('purpose', 'verification')
        
        if not email or not otp_code:
            return jsonify({
                "status": "error",
                "message": "Email and OTP code are required"
            }), 400
        
        # Verify OTP
        success, message = OTPGenerator.verify_email_otp(email, otp_code, purpose)
        
        if not success:
            return jsonify({
                "status": "error",
                "message": message
            }), 400
        
        return jsonify({
            "status": "success",
            "message": "OTP verified successfully",
            "verified": True
        }), 200
        
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/api/email/resend-otp", methods=["POST"])
def resend_otp():
    """Resend OTP to email"""
    try:
        data = request.get_json()
        email = data.get('email')
        purpose = data.get('purpose', 'verification')
        
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400
        
        # Check rate limit (stricter for resend)
        can_proceed, rate_message = OTPGenerator.check_rate_limit(
            email, purpose, max_requests=3, time_window_minutes=30
        )
        if not can_proceed:
            return jsonify({"status": "error", "message": rate_message}), 429
        
        # Create new OTP
        otp_record = OTPGenerator.create_email_otp(email, purpose)
        
        # Send email
        success, message = email_service.send_otp_email(email, otp_record.otp_code, purpose)
        
        if not success:
            logger.error(f"Failed to resend OTP email: {message}")
            return jsonify({
                "status": "error",
                "message": "Failed to resend OTP email. Please try again."
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "OTP resent successfully",
            "expires_in_minutes": 10
        }), 200
        
    except Exception as e:
        logger.error(f"Resend OTP error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
