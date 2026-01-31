from datetime import datetime
from db import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default="customer", nullable=False)  # 'admin' or 'customer'
    status = db.Column(db.String(10), default="inactive", nullable=False)  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # products = db.relationship("Product", backref="seller", lazy=True)
    carts = db.relationship("Cart", backref="users", lazy=True)
    # wishlists = db.relationship("Wishlist", backref="user", lazy=True)
    reviews = db.relationship("Review", backref="users", lazy=True)


    def __repr__(self):
        return f"<User {self.email} - {self.status}>"
