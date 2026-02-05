from flask import jsonify, current_app as app
from auth import auth
from models.orders import Order
from db import db

@app.route("/api/orders/count/<string:user_id>", methods=["GET"])
@auth
def get_orders_count(current_user, user_id):
    """Get total count of orders for a specific user"""
    try:
        # Security check: Ensure querying user matches current user or is admin
        # Converting IDs to strings for comparison just in case
        if str(current_user.user_id) != str(user_id) and current_user.role != 'admin':
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
            
        count = Order.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "count": count
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
