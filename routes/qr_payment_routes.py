# routes/qr_payment_routes.py
from flask import request, jsonify, current_app as app, send_file
from auth import auth
from models.orders import Order
from models.qr_payment import QRPayment
from models.payment_details import PaymentDetail
from utils.qr_generator import QRGenerator
from db import db
from datetime import datetime
import logging
import os
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

@app.route("/api/payment/qr/generate", methods=["POST"])
@auth
def generate_qr_payment(current_user):
    """Generate UPI QR code for order payment"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({"status": "error", "message": "Order ID is required"}), 400
        
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Check if payment is already completed
        if order.payment_status == 'completed':
            return jsonify({
                "status": "error",
                "message": "Payment already completed"
            }), 400
        
        # Get merchant UPI ID from environment
        merchant_upi = os.environ.get('MERCHANT_UPI_ID', 'merchant@upi')
        
        # Create QR payment record
        qr_payment = QRPayment(
            order_id=order.id,
            upi_id=merchant_upi,
            amount=order.total_amount,
            expiry_minutes=15
        )
        
        # Generate QR code image
        upi_string, qr_image_base64 = QRGenerator.generate_upi_qr_code(
            upi_id=merchant_upi,
            amount=float(order.total_amount),
            payee_name="MapMarket",
            transaction_note=f"Order {order.order_number}"
        )
        
        qr_payment.qr_code_image = qr_image_base64
        
        db.session.add(qr_payment)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "QR code generated successfully",
            "qr_payment": qr_payment.to_dict(include_qr_data=True),
            "order_number": order.order_number
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Generate QR payment error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/qr/<string:qr_id>/status", methods=["GET"])
@auth
def get_qr_payment_status(current_user, qr_id):
    """Poll QR payment status"""
    try:
        qr_payment = QRPayment.query.filter_by(qr_id=qr_id).first_or_404()
        
        # Get associated order
        order = Order.query.get(qr_payment.order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Check if expired
        if qr_payment.is_expired() and qr_payment.status == 'pending':
            qr_payment.mark_expired()
            db.session.commit()
        
        return jsonify({
            "status": "success",
            "qr_payment": qr_payment.to_dict(include_qr_data=False),
            "order_status": order.order_status,
            "payment_status": order.payment_status
        }), 200
        
    except Exception as e:
        logger.error(f"Get QR payment status error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/qr/<string:qr_id>/verify", methods=["POST"])
@auth
def verify_qr_payment(current_user, qr_id):
    """Verify QR payment (manual verification or webhook)"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        transaction_ref = data.get('transaction_ref')
        
        if not transaction_id:
            return jsonify({
                "status": "error",
                "message": "Transaction ID is required"
            }), 400
        
        qr_payment = QRPayment.query.filter_by(qr_id=qr_id).first_or_404()
        
        # Get associated order
        order = Order.query.get(qr_payment.order_id)
        
        # Check if order belongs to current user (or admin)
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Check if already verified
        if qr_payment.status == 'completed':
            return jsonify({
                "status": "error",
                "message": "Payment already verified"
            }), 400
        
        # Check if expired
        if qr_payment.is_expired():
            return jsonify({
                "status": "error",
                "message": "QR code has expired"
            }), 400
        
        # Mark payment as completed
        qr_payment.mark_completed(transaction_id, transaction_ref)
        
        # Update order payment status
        order.payment_status = 'completed'
        order.payment_reference = transaction_id
        
        # Create payment detail record
        payment_detail = PaymentDetail(
            user_id=current_user.id,
            order_id=order.id,
            payment_method='qr_code',
            payment_mode='upi',
            upi_id=qr_payment.upi_id,
            gateway_name='qr_payment',
            qr_payment_id=qr_payment.id,
            gateway_response={
                "transaction_id": transaction_id,
                "transaction_ref": transaction_ref,
                "verified_at": datetime.utcnow().isoformat()
            },
            payment_verified_at=datetime.utcnow()
        )
        
        db.session.add(payment_detail)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Payment verified successfully",
            "qr_payment": qr_payment.to_dict(include_qr_data=False),
            "order": order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Verify QR payment error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/qr/<string:qr_id>/image", methods=["GET"])
@auth
def get_qr_code_image(current_user, qr_id):
    """Get QR code image"""
    try:
        qr_payment = QRPayment.query.filter_by(qr_id=qr_id).first_or_404()
        
        # Get associated order
        order = Order.query.get(qr_payment.order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        if not qr_payment.qr_code_image:
            return jsonify({
                "status": "error",
                "message": "QR code image not found"
            }), 404
        
        # Decode base64 image
        img_data = base64.b64decode(qr_payment.qr_code_image)
        
        return send_file(
            BytesIO(img_data),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'qr_payment_{qr_id}.png'
        )
        
    except Exception as e:
        logger.error(f"Get QR code image error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
