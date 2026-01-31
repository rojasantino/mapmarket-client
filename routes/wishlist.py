from flask import request, jsonify, current_app as app
from models.wishlists import Wishlist
from models.products import Product
from db import db
from auth import auth

@app.route("/api/wishlist", methods=["GET"])
@auth
def get_wishlist(current_user):
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        "status": "success",
        "data": [item.to_dict() for item in wishlist_items]
    })


# routes/wishlist.py (update the add_to_wishlist function)
@app.route("/api/wishlist", methods=["POST"])
@auth
def add_to_wishlist(current_user):
    data = request.get_json()
    product_id = data.get("product_id")
    
    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if existing:
        return jsonify({"message": "Already in wishlist"}), 200

    # Get the product to copy its image_filename
    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    new_item = Wishlist(
        user_id=current_user.id,
        product_id=product_id,
        image_filename=product.image_filename  # Copy the image_filename from product
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": "Added to wishlist"}), 201

@app.route("/api/wishlist/<string:product_id>", methods=["DELETE"])
@auth
def remove_from_wishlist(current_user, product_id):
    item = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if not item:
        return jsonify({"error": "Wishlist item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Removed from wishlist"}), 200
