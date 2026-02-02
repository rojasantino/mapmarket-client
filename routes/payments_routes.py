from flask import request, jsonify, current_app as app
from polars import datetime
from db import db
from models.billing import BillingInfo
from models.orders import Order
from models.payment_details import PaymentDetail

from models.reviews import Review
from models.products import Product

import random
from auth import auth
import logging
from datetime import datetime


@app.route("/api/billing", methods=["POST"])
@auth
def save_billing_info(current_user):
    try:
        data = request.get_json()
        
        # Check if user already has billing info
        existing_billing = BillingInfo.query.filter_by(
            user_id=current_user.id,
            is_primary=True
        ).first()
        
        if existing_billing:
            # Update existing primary billing info
            update_fields = [
                'first_name', 'last_name', 'email', 'phone',
                'street_address', 'city', 'state', 'zip_code', 'country'
            ]
            
            for field in update_fields:
                if field in data:
                    setattr(existing_billing, field, data[field])
            
            existing_billing.updated_at = datetime.utcnow()
            billing = existing_billing
        else:
            # Create new billing info
            data['user_id'] = current_user.id
            data['is_primary'] = True
            billing = BillingInfo(**data)
            db.session.add(billing)
        
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Billing info saved successfully",
            "data": billing.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/billing/<int:billing_id>", methods=["PUT"])
@auth
def update_billing_info(current_user, billing_id):
    try:
        billing = BillingInfo.query.get_or_404(billing_id)
        
        # Check if billing info belongs to current user
        if billing.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
        data = request.get_json()
        
        # Update fields
        update_fields = [
            'first_name', 'last_name', 'email', 'phone',
            'street_address', 'city', 'state', 'zip_code', 'country'
        ]
        
        for field in update_fields:
            if field in data:
                setattr(billing, field, data[field])
        
        billing.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Billing info updated successfully",
            "data": billing.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/billing/<int:billing_id>", methods=["GET"])
@auth
def get_billing_info(current_user, billing_id):
    try:
        billing = BillingInfo.query.get_or_404(billing_id)
        
        # Check if billing info belongs to current user
        if billing.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
            
        return jsonify({
            "status": "success", 
            "data": billing.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/billing/user", methods=["GET"])
@auth
def get_user_billing_info(current_user):
    try:
        # Get all billing info for the current user, latest first
        billing_list = BillingInfo.query.filter_by(user_id=current_user.id)\
            .order_by(BillingInfo.updated_at.desc())\
            .all()
        
        # If no billing info exists, return empty array
        if not billing_list:
            return jsonify({
                "status": "success", 
                "data": [],
                "message": "No billing information found"
            }), 200
            
        return jsonify({
            "status": "success", 
            "data": [billing.to_dict() for billing in billing_list]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/billing/primary", methods=["GET"])
@auth
def get_primary_billing_info(current_user):
    try:
        # Get primary billing info for the current user
        billing = BillingInfo.query.filter_by(
            user_id=current_user.id,
            is_primary=True
        ).first()
        
        if not billing:
            return jsonify({
                "status": "success", 
                "data": None,
                "message": "No primary billing information found"
            }), 200
            
        return jsonify({
            "status": "success", 
            "data": billing.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# In your Flask app routes
@app.route("/api/orders", methods=["POST"])
@auth
def create_order(current_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['items', 'total_amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Create order
        order = Order(
            user_id=current_user.id,
            billing_info_id=data.get('billing_info_id'),  # Include billing_info_id
            items=data['items'],
            total_amount=data['total_amount'],
            payment_method=data['payment_method'],
            payment_status=data.get('payment_status', 'pending'),
            order_status=data.get('order_status', 'placed')
        )

        db.session.add(order)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Order created successfully",
            "order": order.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders/<int:order_id>", methods=["GET"])
@auth
def get_order(current_user, order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Optional: Check if order belongs to current user
        # if order.user_id != current_user.id:
        #     return jsonify({"error": "Unauthorized"}), 403

        return jsonify({
            "status": "success",
            "order": order.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @app.route("/api/orders/<string:order_number>", methods=["GET"])
# @auth
# def get_order(current_user, order_number):
#     order = Order.query.filter_by(
#         order_number=order_number,
#         user_id=current_user.id
#     ).first_or_404()

#     return jsonify({
#         "status": "success",
#         "order": order.to_dict()
#     }), 200



@app.route("/api/orders/user/<int:user_id>", methods=["GET"])
@auth
def get_orders_by_user(current_user, user_id):
    if current_user.id != user_id:
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    orders = Order.query.filter_by(user_id=user_id).all()

    if not orders:
        return jsonify({"status": "error", "message": "No orders found"}), 404

    return jsonify({
        "status": "success",
        "count": len(orders),
        "orders": [order.to_dict() for order in orders]
    }), 200


# Configure logger
logger = logging.getLogger(__name__)

@app.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
@auth
def cancel_order(current_user, order_id):
    try:
        data = request.get_json()
        reason = data.get("reason", "").strip()

        logger.info(f"Cancel request for order {order_id} from user {current_user.id}")

        if not reason:
            logger.warning(f"Missing cancellation reason for order {order_id}")
            return jsonify({"error": "Cancellation reason is required"}), 400

        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

        if not order:
            logger.warning(f"Order {order_id} not found for user {current_user.id}")
            return jsonify({"error": "Order not found"}), 404

        if order.order_status == "cancelled":
            logger.info(f"Order {order_id} is already cancelled")
            return jsonify({"error": "Order already cancelled"}), 400

        # Check if order can be cancelled
        non_cancellable_statuses = ['shipped', 'out_for_delivery', 'delivered']
        if order.order_status in non_cancellable_statuses:
            logger.warning(f"Cannot cancel order {order_id} with status {order.order_status}")
            return jsonify({
                "error": f"Cannot cancel order that is already {order.order_status}"
            }), 400

        # Update order fields
        order.order_status = "cancelled"
        order.cancel_reason = reason
        order.cancelled_at = datetime.utcnow()

        # Handle refund for non-COD payments
        refund_info = None
        if order.payment_method != 'cod' and order.payment_status == 'completed':
            order.payment_status = 'refund_pending'
            refund_info = {
                "message": "Refund will be processed within 5-7 business days",
                "method": "original_payment_method",
                "status": "pending"
            }
            logger.info(f"Refund initiated for order {order_id}")

        db.session.commit()
        logger.info(f"Order {order_id} cancelled successfully by user {current_user.id}")

        # Prepare response
        response_data = {
            "status": "success",
            "message": "Order cancelled successfully",
            "order": order.to_dict()
        }
        
        if refund_info:
            response_data["refund_info"] = refund_info

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling order {order_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    
    


@app.route("/api/payment/initiate", methods=["POST"])
@auth
def initiate_payment(current_user):
    data = request.get_json()
    order_id = data["order_id"]
    payment_method = data["payment_method"]

    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()

    if not order:
        return jsonify({"status": "error", "message": "Order not found"}), 404

    fake_reference = f"PAY-{random.randint(10000, 99999)}"

    payment = PaymentDetail(
        user_id=current_user.id,
        order_id=order_id,
        payment_method=payment_method,
        payment_mode=data.get("payment_mode"),
        upi_id=data.get("upi_id"),
        cardholder_name=data.get("cardholder_name"),
        masked_card_number=data.get("masked_card_number"),
        gateway_name="Razorpay (Sandbox)",
        gateway_response={"status": "initiated", "reference": fake_reference}
    )

    db.session.add(payment)
    db.session.commit()

    order.payment_reference = fake_reference
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Payment initiated successfully",
        "payment_reference": fake_reference
    })


@app.route("/api/payment/callback", methods=["POST"])
def payment_callback():
    data = request.get_json()
    payment_reference = data.get("payment_reference")
    payment_status = data.get("payment_status", "success")

    order = Order.query.filter_by(payment_reference=payment_reference).first()

    if not order:
        return jsonify({"status": "error", "message": "Order not found"}), 404

    order.payment_status = payment_status
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Payment status updated",
        "order": order.to_dict()
    }), 200

@app.route("/api/orders/<string:order_number>/track", methods=["GET"])
@auth
def track_order(current_user, order_number):
    order = Order.query.filter_by(
        order_number=order_number,
        user_id=current_user.id
    ).first()

    if not order:
        return jsonify({"error": "Order not found"}), 404

    timeline = [
        {"status": "placed", "label": "Order Confirmed"},
        {"status": "shipped", "label": "Shipped"},
        {"status": "out_for_delivery", "label": "Out for Delivery"},
        {"status": "delivered", "label": "Delivered"}
    ]

    return jsonify({
        "status": "success",
        "order_id": order.order_number,
        "current_status": order.order_status,
        "timeline": timeline
    }), 200



# orders ratings

@app.route("/api/orders/<string:order_id>/rate", methods=["POST"])
@auth
def rate_order_products(current_user, order_id):
    try:
        data = request.get_json()
        if not data or "ratings" not in data:
            return jsonify({"error": "Ratings data is required"}), 400

        # Find order by order_number
        order = Order.query.filter_by(order_number=order_id, user_id=current_user.id).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404

        if order.order_status != "delivered":
            return jsonify({"error": "Only delivered orders can be rated"}), 400

        created_reviews = []
        for rating_item in data["ratings"]:
            product_id = rating_item.get("product_id")
            rate = rating_item.get("rate")
            description = rating_item.get("description", "")

            if not product_id or rate is None:
                return jsonify({"error": "Each rating must include product_id and rate"}), 400

            # Check if product exists
            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": f"Product {product_id} not found"}), 404

            # Check if the user actually bought this product
            purchased = any(item.get("product_id") == product_id for item in order.items)
            if not purchased:
                return jsonify({"error": f"You can only rate products you purchased. Product {product_id} not in your order."}), 403

            # Check if review exists
            existing_review = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            if existing_review:
                existing_review.rates = rate
                existing_review.description = description
                existing_review.verified = True
                db.session.add(existing_review)
                created_reviews.append(existing_review)
            else:
                review = Review(
                    user_id=current_user.id,
                    product_id=product_id,
                    username=current_user.username,
                    rates=rate,
                    description=description,
                    verified=True
                )
                db.session.add(review)
                created_reviews.append(review)

        db.session.commit()
        return jsonify({
            "status": "success",
            "message": f"Rated {len(created_reviews)} product(s) successfully",
            "reviews": [{
                "id": r.id,
                "product_id": r.product_id,
                "rate": r.rates,
                "description": r.description,
                "verified": r.verified,
                "created_at": r.created_at.isoformat()
            } for r in created_reviews]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/products/<int:product_id>/ratings", methods=["GET"])
def get_product_ratings(product_id):
    try:
        reviews = Review.query.filter_by(product_id=product_id).all()
        
        if not reviews:
            return jsonify({
                "status": "success",
                "average_rating": 0,
                "total_reviews": 0,
                "ratings_breakdown": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "reviews": []
            }), 200
        
        # Calculate average rating
        total_rating = sum(review.rates for review in reviews)
        average_rating = total_rating / len(reviews)
        
        # Calculate ratings breakdown
        ratings_breakdown = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        for review in reviews:
            ratings_breakdown[str(review.rates)] += 1
        
        return jsonify({
            "status": "success",
            "average_rating": round(average_rating, 1),
            "total_reviews": len(reviews),
            "ratings_breakdown": ratings_breakdown,
            "reviews": [{
                "id": review.id,
                "user_id": review.user_id,
                "username": review.username,
                "rate": review.rates,
                "description": review.description,
                "verified": review.verified,
                "created_at": review.created_at.isoformat()
            } for review in reviews]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500