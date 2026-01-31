from flask import request, jsonify, current_app as app
from auth import encode_auth_token
from auth import auth  
from models.signup import Signup
from models.users import User
from models.products import Product
from db import db
from sqlalchemy import distinct
from oauth import get_google_auth_url, exchange_code_for_token, verify_google_token

@app.route("/api/products", methods=["GET"])
def get_all_products():
    products = Product.query.all()
    product_list = [product.to_dict() for product in products]

    return jsonify({
        "status": "success",
        "count": len(product_list),
        "data": product_list
    }), 200



@app.route("/api/products/<string:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    return jsonify({
        "status": "success",
        "data": product.to_dict()
    }), 200


@app.route("/api/products/<string:product_id>/stock", methods=["GET"])
def get_product_stock(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if not product:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    return jsonify({
        "status": "success",
        "product_id": product.product_id,
        "stock": product.stock
    }), 200


@app.route("/api/products/filters", methods=["GET"])
def get_product_filters():
    """Get dynamic filter options from products"""
    
    # Get unique categories
    categories = db.session.query(distinct(Product.category)).filter(Product.category.isnot(None)).all()
    category_list = [cat[0] for cat in categories if cat[0]]
    
    # Get unique materials/formats
    all_materials = set()
    products = Product.query.all()
    
    for product in products:
        if product.material:  # Changed from product.format to product.material
            # Handle different material storage formats
            if isinstance(product.material, list):
                for material in product.material:
                    if material:
                        all_materials.add(material.strip())
            elif isinstance(product.material, str):
                # Try to parse as JSON
                try:
                    import json
                    materials = json.loads(product.material)
                    if isinstance(materials, list):
                        for material in materials:
                            if material:
                                all_materials.add(material.strip())
                except:
                    # Treat as comma-separated string
                    materials = product.material.split(',')
                    for material in materials:
                        if material.strip():
                            all_materials.add(material.strip())
    
    material_list = sorted(list(all_materials))
    
    # Get price ranges
    min_price = db.session.query(db.func.min(Product.price)).scalar() or 0
    max_price = db.session.query(db.func.max(Product.price)).scalar() or 10000
    
    return jsonify({
        "status": "success",
        "filters": {
            "categories": category_list,
            "formats": material_list,  # Changed from formats to materials
            "price_range": {
                "min": float(min_price),
                "max": float(max_price)
            }
        }
    }), 200


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    required_fields = ["name", "email", "password", "phone"]

    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if Signup.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    full_name = data["name"].strip()
    parts = full_name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    new_user = Signup(
        name=full_name,
        email=data["email"],
        phone=data["phone"]
    )
    new_user.set_password(data["password"])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "user_id": new_user.user_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": new_user.email,
            "phone": new_user.phone,
            "role": new_user.role,
            "created_at": new_user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
    }), 201


# # this is store in users table

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    identifier = data.get("email")  # can be name, email, or phone
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"error": "Name/Email/Phone and password required"}), 400

    # ✅ Try matching in order: email → phone → name
    if "@" in identifier:
        signup_user = Signup.query.filter_by(email=identifier).first()
    elif identifier.isdigit():
        signup_user = Signup.query.filter_by(phone=identifier).first()
    else:
        signup_user = Signup.query.filter_by(name=identifier).first()

    if not signup_user or not signup_user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # ✅ Ensure user exists in users table
    user = User.query.filter_by(email=signup_user.email).first()
    if not user:
        user = User(
            email=signup_user.email,
            password=signup_user.password_hash,
            role=signup_user.role,
            status="active",
            user_id=signup_user.user_id
        )
        db.session.add(user)
    else:
        user.status = "active"

    db.session.commit()

    # ✅ Generate JWT token
    token = encode_auth_token(user.id)

    return jsonify({
        "message": "Login successful",
        "token": str(token),
        "user": {
            "id": user.id,
            "user_id": signup_user.user_id,
            "name": signup_user.name,
            "email": user.email,
            "phone": signup_user.phone,
            "status": user.status
        }
    }), 200


# oauthentications 

@app.route("/api/oauth/google/url", methods=["GET"])
def get_google_oauth_url():
    """Get Google OAuth URL for frontend"""
    url = get_google_auth_url()
    return jsonify({
        "url": url,
        "client_id": GOOGLE_CLIENT_ID
    }), 200

@app.route("/api/oauth/google/callback", methods=["POST"])
def google_oauth_callback():
    """Handle Google OAuth callback with authorization code"""
    data = request.get_json()
    code = data.get("code")
    
    if not code:
        return jsonify({"error": "Authorization code required"}), 400
    
    # Exchange code for token
    access_token = exchange_code_for_token(code)
    if not access_token:
        return jsonify({"error": "Failed to exchange code for token"}), 400
    
    # Verify token and get user info
    oauth_user = verify_google_token(access_token)
    if not oauth_user:
        return jsonify({"error": "Invalid OAuth token"}), 401
    
    # Continue with your existing OAuth login logic
    return oauth_login_handler(oauth_user)

def oauth_login_handler(oauth_user):
    """Common handler for OAuth login (used by both direct token and code flow)"""
    # Match or create user in signup table
    signup_user = Signup.query.filter_by(email=oauth_user["email"]).first()
    
    # If signup does NOT exist → auto-register
    if not signup_user:
        signup_user = Signup(
            name=oauth_user["name"],
            email=oauth_user["email"],
            password_hash=None,
            role="user",
            user_id=f"GOOGLE-{oauth_user['provider_id']}",
            phone=None,  # OAuth users might not have phone
            avatar=oauth_user.get("picture")  # Store profile picture
        )
        db.session.add(signup_user)
        db.session.commit()
    
    # Ensure user exists in users table
    user = User.query.filter_by(email=signup_user.email).first()
    if not user:
        user = User(
            email=signup_user.email,
            password=None,
            role=signup_user.role,
            status="active",
            user_id=signup_user.user_id
        )
        db.session.add(user)
    else:
        user.status = "active"
    
    db.session.commit()
    
    # Generate JWT token
    token = encode_auth_token(user.id)
    
    return jsonify({
        "message": "OAuth login successful",
        "token": token,
        "user": {
            "id": user.id,
            "user_id": signup_user.user_id,
            "name": signup_user.name,
            "email": user.email,
            "avatar": signup_user.avatar,
            "status": user.status,
            "oauth": True,
            "provider": oauth_user.get("provider", "google")
        }
    }), 200

@app.route("/api/oauth/login", methods=["POST"])
def oauth_login():
    """Direct OAuth login with access token (for mobile/desktop apps)"""
    data = request.get_json()
    access_token = data.get("access_token")
    provider = data.get("provider", "google")  # Support multiple providers
    
    if not access_token:
        return jsonify({"error": "OAuth token required"}), 400
    
    # Verify the token
    if provider == "google":
        oauth_user = verify_google_token(access_token)
    else:
        return jsonify({"error": "Unsupported OAuth provider"}), 400
    
    if not oauth_user or not oauth_user.get("email"):
        return jsonify({"error": "Invalid OAuth token"}), 401
    
    return oauth_login_handler(oauth_user)







@app.route("/api/profile", methods=["GET"])
@auth
def profile(current_user):
    signup_user = Signup.query.filter_by(email=current_user.email).first()
    return jsonify({
        "id": current_user.id,
        "name": signup_user.name if signup_user else None,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status
    }), 200


@app.route("/api/logout", methods=["POST"])
@auth
def logout(current_user):
    current_user.status = "inactive"
    db.session.commit()
    return jsonify({"message": "Logout successful", "status": current_user.status}), 200
