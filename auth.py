# auth.py

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app as app
import requests
from models.users import User
import jwt

def auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        print("Authorization header:", token)
        if not token:
            return jsonify({"message": "Token is missing !!"}), 401

        if token.startswith("Bearer "):
            # token = token[7:]
            token = token.split(" ")[1]

        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
            user_id = int(payload["sub"])  # convert string back to int
            user = User.query.get(user_id)
            if not user:
                return jsonify({"message": "User not found !!"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired !!"}), 401
        except Exception as e:
            print(e)
            return jsonify({"message": "Token is invalid !!"}), 401

        # pass actual User object
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
            "sub": str(user_id)   # MUST be a string
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")
        # PyJWT 2.x may return bytes
        return token if isinstance(token, str) else token.decode("utf-8")
    except Exception as e:
        return str(e)

