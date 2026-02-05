# routes/payment_integration_routes.py
from flask import request, jsonify, current_app as app
from auth import auth
from models.orders import Order
from models.payment_details import PaymentDetail
from models.order_timeline import OrderTimeline
from utils.payment_gateway import RazorpayGateway, StripeGateway
from db import db
from datetime import datetime
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

# Initialize payment gateways
razorpay_gateway = RazorpayGateway()
stripe_gateway = StripeGateway()

# ==================== RAZORPAY ROUTES ====================

@app.route("/api/payment/razorpay/create-order", methods=["POST"])
@auth
def create_razorpay_order(current_user):
    """Create Razorpay order"""
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
        
        # Create Razorpay order
        success, result = razorpay_gateway.create_order(
            amount=float(order.total_amount),
            currency='INR',
            receipt=order.order_number,
            notes={
                'order_id': order.id,
                'order_number': order.order_number,
                'user_id': current_user.id
            }
        )
        
        if not success:
            logger.error(f"Razorpay order creation failed: {result}")
            return jsonify({
                "status": "error",
                "message": "Failed to create payment order"
            }), 500
        
        # Save Razorpay order ID
        payment_detail = PaymentDetail(
            user_id=current_user.id,
            order_id=order.id,
            payment_method='razorpay',
            gateway_name='razorpay',
            razorpay_order_id=result['id'],
            gateway_response=result
        )
        
        db.session.add(payment_detail)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Razorpay order created successfully",
            "razorpay_order_id": result['id'],
            "amount": result['amount'],
            "currency": result['currency'],
            "key_id": razorpay_gateway.key_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create Razorpay order error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/razorpay/verify", methods=["POST"])
@auth
def verify_razorpay_payment(current_user):
    """Verify Razorpay payment signature"""
    try:
        data = request.get_json()
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return jsonify({
                "status": "error",
                "message": "Missing required payment details"
            }), 400
        
        # Find payment detail
        payment_detail = PaymentDetail.query.filter_by(
            razorpay_order_id=razorpay_order_id
        ).first_or_404()
        
        order = Order.query.get(payment_detail.order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Verify signature
        is_valid = razorpay_gateway.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if not is_valid:
            logger.warning(f"Invalid Razorpay signature for order {order.order_number}")
            return jsonify({
                "status": "error",
                "message": "Invalid payment signature"
            }), 400
        
        # Update payment details
        payment_detail.razorpay_payment_id = razorpay_payment_id
        payment_detail.razorpay_signature = razorpay_signature
        payment_detail.payment_verified_at = datetime.utcnow()
        
        # Update order
        order.payment_status = 'completed'
        order.payment_reference = razorpay_payment_id
        
        # Create timeline entry
        OrderTimeline.create_timeline_entry(
            order_id=order.id,
            status='payment_completed',
            description="Payment completed via Razorpay",
            updated_by="system"
        )
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Payment verified successfully",
            "order": order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Verify Razorpay payment error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/webhook/razorpay", methods=["POST"])
def razorpay_webhook():
    """Handle Razorpay webhooks"""
    try:
        # Get webhook signature
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = app.config.get('RAZORPAY_WEBHOOK_SECRET', '')
        
        # Verify webhook signature
        payload = request.get_data()
        expected_signature = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if webhook_signature != expected_signature:
            logger.warning("Invalid Razorpay webhook signature")
            return jsonify({"status": "error", "message": "Invalid signature"}), 400
        
        # Process webhook event
        data = request.get_json()
        event = data.get('event')
        payload_data = data.get('payload', {}).get('payment', {}).get('entity', {})
        
        logger.info(f"Razorpay webhook event: {event}")
        
        # Handle different events
        if event == 'payment.captured':
            # Payment successful
            razorpay_payment_id = payload_data.get('id')
            razorpay_order_id = payload_data.get('order_id')
            
            payment_detail = PaymentDetail.query.filter_by(
                razorpay_order_id=razorpay_order_id
            ).first()
            
            if payment_detail:
                payment_detail.razorpay_payment_id = razorpay_payment_id
                payment_detail.payment_verified_at = datetime.utcnow()
                
                order = Order.query.get(payment_detail.order_id)
                order.payment_status = 'completed'
                order.payment_reference = razorpay_payment_id
                
                db.session.commit()
        
        elif event == 'payment.failed':
            # Payment failed
            razorpay_order_id = payload_data.get('order_id')
            
            payment_detail = PaymentDetail.query.filter_by(
                razorpay_order_id=razorpay_order_id
            ).first()
            
            if payment_detail:
                order = Order.query.get(payment_detail.order_id)
                order.payment_status = 'failed'
                db.session.commit()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Razorpay webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== STRIPE ROUTES ====================

@app.route("/api/payment/stripe/create-intent", methods=["POST"])
@auth
def create_stripe_payment_intent(current_user):
    """Create Stripe payment intent"""
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
        
        # Create Stripe payment intent
        success, result = stripe_gateway.create_payment_intent(
            amount=float(order.total_amount),
            currency='inr',
            metadata={
                'order_id': order.id,
                'order_number': order.order_number,
                'user_id': current_user.id
            }
        )
        
        if not success:
            logger.error(f"Stripe payment intent creation failed: {result}")
            return jsonify({
                "status": "error",
                "message": "Failed to create payment intent"
            }), 500
        
        # Save Stripe payment intent ID
        payment_detail = PaymentDetail(
            user_id=current_user.id,
            order_id=order.id,
            payment_method='stripe',
            gateway_name='stripe',
            stripe_payment_intent_id=result['id'],
            gateway_response=dict(result)
        )
        
        db.session.add(payment_detail)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Payment intent created successfully",
            "client_secret": result['client_secret'],
            "payment_intent_id": result['id']
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create Stripe payment intent error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/stripe/confirm", methods=["POST"])
@auth
def confirm_stripe_payment(current_user):
    """Confirm Stripe payment"""
    try:
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({
                "status": "error",
                "message": "Payment intent ID is required"
            }), 400
        
        # Find payment detail
        payment_detail = PaymentDetail.query.filter_by(
            stripe_payment_intent_id=payment_intent_id
        ).first_or_404()
        
        order = Order.query.get(payment_detail.order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Retrieve payment intent from Stripe
        success, intent = stripe_gateway.retrieve_payment_intent(payment_intent_id)
        
        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to retrieve payment intent"
            }), 500
        
        # Check payment status
        if intent['status'] == 'succeeded':
            payment_detail.payment_verified_at = datetime.utcnow()
            payment_detail.stripe_charge_id = intent.get('latest_charge')
            
            order.payment_status = 'completed'
            order.payment_reference = payment_intent_id
            
            # Create timeline entry
            OrderTimeline.create_timeline_entry(
                order_id=order.id,
                status='payment_completed',
                description="Payment completed via Stripe",
                updated_by="system"
            )
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Payment confirmed successfully",
                "order": order.to_dict()
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": f"Payment status: {intent['status']}"
            }), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Confirm Stripe payment error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/payment/webhook/stripe", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET', '')
        
        # Verify webhook signature
        success, event = stripe_gateway.verify_webhook_signature(
            payload, sig_header, webhook_secret
        )
        
        if not success:
            logger.warning(f"Invalid Stripe webhook signature: {event}")
            return jsonify({"status": "error", "message": "Invalid signature"}), 400
        
        logger.info(f"Stripe webhook event: {event['type']}")
        
        # Handle different events
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']
            
            payment_detail = PaymentDetail.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment_detail:
                payment_detail.payment_verified_at = datetime.utcnow()
                payment_detail.stripe_charge_id = payment_intent.get('latest_charge')
                
                order = Order.query.get(payment_detail.order_id)
                order.payment_status = 'completed'
                order.payment_reference = payment_intent_id
                
                db.session.commit()
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']
            
            payment_detail = PaymentDetail.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment_detail:
                order = Order.query.get(payment_detail.order_id)
                order.payment_status = 'failed'
                db.session.commit()
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
