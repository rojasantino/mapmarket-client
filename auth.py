# auth.py

from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from models.users import User
import jwt

# 🔐 move this to env later
SECRET_KEY = "secret"


def auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        print("Authorization header:", auth_header)

        # 1️⃣ Missing header
        if not auth_header:
            return jsonify({"message": "Authorization header missing"}), 401

        # 2️⃣ Invalid format
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Invalid authorization format"}), 401

        # 3️⃣ Extract token
        token = auth_header.split(" ")[1]

        try:
            # 4️⃣ Decode token (PyJWT)
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=["HS256"]
            )

            # 5️⃣ Get user
            user_id = int(payload.get("sub"))
            user = User.query.get(user_id)

            if not user:
                return jsonify({"message": "User not found"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        except Exception as e:
            # Safety net – prevents 500
            print("AUTH ERROR:", e)
            return jsonify({"message": "Authentication failed"}), 401

        # 6️⃣ Pass user to route
        return f(user, *args, **kwargs)

    return decorated


def encode_auth_token(user_id):
    """
    Generates JWT Auth Token
    """
    try:
        payload = {
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
            "sub": str(user_id)  # MUST be string per JWT spec
        }

        token = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm="HS256"
        )

        # PyJWT 2.x returns str (keep compatibility)
        return token

    except Exception as e:
        print("TOKEN ENCODE ERROR:", e)
        return None
