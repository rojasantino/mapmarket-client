# oauth.py
import os
import requests
from flask import current_app
from functools import wraps
import json

GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

def get_google_auth_url():
    """Generate Google OAuth URL for frontend"""
    scopes = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent"
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    return auth_url

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    try:
        payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=payload)
        data = response.json()
        
        if response.status_code != 200:
            print(f"Token exchange error: {data}")
            return None
            
        return data.get("access_token")
    except Exception as e:
        print(f"Token exchange exception: {e}")
        return None

def verify_google_token(access_token):
    """Verify Google access token and get user info"""
    try:
        if current_app.config.get('DEBUG') and access_token.startswith('mock_'):
            # Mock response for local testing
            mock_users = {
                "mock_test": {
                    "email": "test@example.com",
                    "name": "Test User",
                    "sub": "mock123"
                },
                "mock_rojas": {
                    "email": "rojasantino7@gmail.com",
                    "name": "Rojas Antino",
                    "sub": "mock456"
                }
            }
            user_key = access_token.replace("mock_", "")
            return mock_users.get(user_key, None)
        
        print(f"[DEBUG] Verifying Google token: {access_token[:20]}...")
        
        response = requests.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        print(f"[DEBUG] Google response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[DEBUG] Google error response: {response.text}")
            return None
        
        data = response.json()
        print(f"[DEBUG] User info received: {json.dumps(data, indent=2)}")
        
        return {
            "email": data.get("email"),
            "name": data.get("name"),
            "provider_id": data.get("sub"),
            "picture": data.get("picture"),
            "provider": "google"
        }
        
    except requests.exceptions.Timeout:
        print("[ERROR] Google API timeout")
        return None
    except Exception as e:
        print(f"[ERROR] OAuth verification failed: {e}")
        return None

def require_oauth(f):
    """Decorator for OAuth-only endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "OAuth token required"}), 401
        
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        
        user_info = verify_google_token(token)
        if not user_info:
            return jsonify({"error": "Invalid OAuth token"}), 401
        
        # Pass user info to the endpoint
        return f(user_info, *args, **kwargs)
    return decorated_function