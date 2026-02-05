# routes/order_tracking_routes.py
from flask import request, jsonify, current_app as app, Response
from auth import auth
from models.orders import Order
from models.order_timeline import OrderTimeline
from utils.email_service import EmailService
from db import db
from datetime import datetime
import random
import json
import logging

logger = logging.getLogger(__name__)
email_service = EmailService()

@app.route("/api/orders/<int:order_id>/timeline", methods=["GET"])
@auth
def get_order_timeline(current_user, order_id):
    """Get complete order timeline/history"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Get timeline entries
        timeline_entries = OrderTimeline.query.filter_by(order_id=order_id)\
            .order_by(OrderTimeline.timestamp.asc()).all()
        
        return jsonify({
            "status": "success",
            "order_id": order.order_number,
            "current_status": order.order_status,
            "timeline": [entry.to_dict() for entry in timeline_entries]
        }), 200
        
    except Exception as e:
        logger.error(f"Get timeline error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/orders/<int:order_id>/update-status", methods=["POST"])
@auth
def update_order_status(current_user, order_id):
    """Update order status (admin or system)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        description = data.get('description', '')
        location = data.get('location', '')
        
        if not new_status:
            return jsonify({"status": "error", "message": "Status is required"}), 400
        
        order = Order.query.get_or_404(order_id)
        
        # Validate status transition
        valid_statuses = ['placed', 'confirmed', 'processing', 'shipped', 
                         'out_for_delivery', 'delivered', 'cancelled', 'returned']
        
        if new_status not in valid_statuses:
            return jsonify({"status": "error", "message": "Invalid status"}), 400
        
        # Update order status
        old_status = order.order_status
        order.order_status = new_status
        
        # Update timestamps based on status
        if new_status == 'confirmed':
            order.confirmed_at = datetime.utcnow()
        elif new_status == 'shipped':
            order.shipped_at = datetime.utcnow()
        elif new_status == 'out_for_delivery':
            order.out_for_delivery_at = datetime.utcnow()
            # Generate delivery OTP
            order.delivery_otp = str(random.randint(1000, 9999))
            # Send delivery notification email
            if order.billing_info:
                email_service.send_delivery_notification(
                    order.billing_info.email,
                    order.order_number,
                    order.delivery_otp,
                    order.estimated_delivery.strftime('%B %d, %Y') if order.estimated_delivery else 'Soon'
                )
        elif new_status == 'delivered':
            order.delivered_at = datetime.utcnow()
        
        # Create timeline entry
        OrderTimeline.create_timeline_entry(
            order_id=order_id,
            status=new_status,
            description=description or f"Order status changed from {old_status} to {new_status}",
            location=location,
            updated_by=current_user.email
        )
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Order status updated successfully",
            "order": order.to_dict(include_timeline=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update status error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/orders/<int:order_id>/delivery/confirm", methods=["POST"])
@auth
def confirm_delivery(current_user, order_id):
    """Confirm delivery with OTP"""
    try:
        data = request.get_json()
        delivery_otp = data.get('delivery_otp')
        
        if not delivery_otp:
            return jsonify({"status": "error", "message": "Delivery OTP is required"}), 400
        
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        # Verify OTP
        if order.delivery_otp != delivery_otp:
            return jsonify({"status": "error", "message": "Invalid delivery OTP"}), 400
        
        # Check if order is out for delivery
        if order.order_status != 'out_for_delivery':
            return jsonify({
                "status": "error",
                "message": "Order is not out for delivery"
            }), 400
        
        # Update order status to delivered
        order.order_status = 'delivered'
        order.delivered_at = datetime.utcnow()
        order.delivery_otp = None  # Clear OTP after use
        
        # Create timeline entry
        OrderTimeline.create_timeline_entry(
            order_id=order_id,
            status='delivered',
            description="Order delivered successfully",
            updated_by=current_user.email
        )
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Delivery confirmed successfully",
            "order": order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Confirm delivery error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/orders/<int:order_id>/track-realtime", methods=["GET"])
@auth
def track_order_realtime(current_user, order_id):
    """Server-Sent Events endpoint for real-time order tracking"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        def generate():
            """Generate SSE events"""
            # Send initial order status
            yield f"data: {json.dumps(order.to_dict(include_timeline=True))}\n\n"
            
            # In a real implementation, this would listen to a message queue (Redis)
            # For now, we'll just send periodic updates
            # This is a simplified version - production would use Redis pub/sub
            
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        logger.error(f"Real-time tracking error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/orders/<int:order_id>/delivery-estimate", methods=["GET"])
@auth
def get_delivery_estimate(current_user, order_id):
    """Get estimated delivery time"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        return jsonify({
            "status": "success",
            "order_id": order.order_number,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "delivery_partner": order.delivery_partner,
            "tracking_number": order.tracking_number
        }), 200
        
    except Exception as e:
        logger.error(f"Get delivery estimate error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
