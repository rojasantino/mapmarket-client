from datetime import datetime
import uuid
from db import db
from werkzeug.security import generate_password_hash, check_password_hash

class Signup(db.Model):
    __tablename__ = "signup"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: f"USR{uuid.uuid4().hex[:8].upper()}")
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(50), default="customer", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # # Relationships
    # products = db.relationship("Product", backref="seller", lazy=True)
    # carts = db.relationship("Cart", backref="users", lazy=True)
    # wishlists = db.relationship("Wishlist", backref="users", lazy=True)
    # reviews = db.relationship("Review", backref="users", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.user_id} - {self.email}>"
