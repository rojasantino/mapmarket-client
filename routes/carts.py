# routes/cart.py
from flask import request, jsonify, current_app as app
from models.cart import Cart
from models.products import Product
from db import db
from auth import auth

TAX_RATE = 0.18
FREE_SHIPPING_THRESHOLD = 800
SHIPPING_COST = 40

def get_cart_item_response(item):
    """Helper function to format cart item response consistently"""
    product = item.product
    
    # Get image URL
    preview_url = None
    image_filename = None
    
    if item.image_filename:
        # Handle both array and string formats
        if isinstance(item.image_filename, list) and len(item.image_filename) > 0:
            primary_image = item.image_filename[0]
            preview_url = f"http://127.0.0.1:5000/static/uploads/products/{primary_image}"
            image_filename = primary_image
        elif isinstance(item.image_filename, str):
            preview_url = f"http://127.0.0.1:5000/static/uploads/products/{item.image_filename}"
            image_filename = item.image_filename
    elif product and product.image_filename:
        # Fallback to product's image
        if isinstance(product.image_filename, list) and len(product.image_filename) > 0:
            primary_image = product.image_filename[0]
            preview_url = f"http://127.0.0.1:5000/static/uploads/products/{primary_image}"
            image_filename = primary_image
        elif isinstance(product.image_filename, str):
            preview_url = f"http://127.0.0.1:5000/static/uploads/products/{product.image_filename}"
            image_filename = product.image_filename
    
    return {
        "cart_id": item.id,
        "user_id": item.user_id,
        "product_id": item.product_id,
        "title": product.title if product else item.title,
        "category": product.category if product else None,
        "size": item.size,
        "qty": item.qty,
        "price": float(product.discounted_price or product.price or 0) if product else float(item.price or 0),
        "discount": float(product.discount or 0) if product else float(item.discount or 0),
        "discounted_price": float(product.discounted_price or product.price or 0) if product else float(item.discounted_price or item.price or 0),
        "stock": int(product.stock or 0) if product else int(item.stock or 0),
        "shipping_cost": float(item.shipping_cost or 0),
        "tax": float(item.tax or 0),
        "total": float(item.total or 0),
        "image_filename": image_filename,
        "previewUrl": preview_url,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

@app.route("/api/cart", methods=["GET"])
@auth
def get_cart(current_user):
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    result = [get_cart_item_response(item) for item in cart_items]
    return jsonify(result), 200

@app.route("/api/cart/<int:user_id>", methods=["GET"])
@auth
def get_cart_by_user(current_user, user_id):
    # 🔐 Security Check — User must match token
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    cart_items = Cart.query.filter_by(user_id=user_id).all()
    result = [get_cart_item_response(item) for item in cart_items]
    
    return jsonify(result), 200

# The rest of your routes remain the same...
@app.route("/api/cart", methods=["POST"])
@auth
def add_to_cart(current_user):
    data = request.get_json()
    product_id = str(data.get("product_id"))
    size = data.get("size")
    qty = int(data.get("quantity", 1))

    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({"error": f"Product {product_id} not found"}), 404

    # Find existing cart item for same user
    existing_item = Cart.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
        size=size
    ).first()

    if existing_item:
        existing_item.qty += qty
        db.session.commit()
        return jsonify({"message": "Cart updated"}), 200

    # Create new cart item with product's image_filename
    new_item = Cart(
        user_id=current_user.id,
        product_id=product.product_id,
        title=product.title,
        size=size,
        price=product.price,
        discount=product.discount,
        discounted_price=product.discounted_price,
        qty=qty,
        stock=product.stock,
        image_filename=product.image_filename,  # This will be JSON array
        shipping_cost=0,
        tax=0,
        total=0
    )

    db.session.add(new_item)
    db.session.commit()

    return jsonify({"message": "Product added to cart"}), 201

@app.route("/api/cart/<string:product_id>", methods=["DELETE"])
@auth
def remove_from_cart(current_user, product_id):
    cart_item = Cart.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if not cart_item:
        return jsonify({"error": "Item not found in your cart"}), 404

    product = Product.query.filter_by(product_id=product_id).first()
    if product:
        product.stock += cart_item.qty

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({"message": "Removed from cart"}), 200

@app.route("/api/cart/<string:product_id>", methods=["PUT"])
@auth
def update_cart_item(current_user, product_id):
    data = request.get_json()
    new_qty = int(data.get("qty", 1))

    cart_item = Cart.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if not cart_item:
        return jsonify({"error": "Item not found in your cart"}), 404

    product = Product.query.filter_by(product_id=product_id).first()

    old_qty = cart_item.qty
    qty_diff = new_qty - old_qty

    if qty_diff > 0:
        if product.stock < qty_diff:
            return jsonify({"error": "Insufficient stock"}), 400
        product.stock -= qty_diff
    else:
        product.stock += abs(qty_diff)

    price = float(product.discounted_price or product.price)
    subtotal = price * new_qty
    tax_amount = subtotal * TAX_RATE
    shipping_cost = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_COST
    total_price = subtotal + tax_amount + shipping_cost

    cart_item.qty = new_qty
    cart_item.tax = tax_amount
    cart_item.shipping_cost = shipping_cost
    cart_item.total = total_price

    db.session.commit()

    return jsonify({
        "product_id": product_id,
        "qty": new_qty,
        "total": total_price
    }), 200