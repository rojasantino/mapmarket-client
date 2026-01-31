# models/wishlist.py
from datetime import datetime
from db import db

class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey("products.product_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Change from String to JSON to match Product model
    image_filename = db.Column(db.JSON, nullable=True)

    product = db.relationship(
        "Product",
        backref="wishlist_items",
        primaryjoin="Wishlist.product_id == Product.product_id",
        foreign_keys=[product_id]
    )

    def get_primary_image(self):
        """Get the primary image filename from the image_filename array"""
        if not self.image_filename:
            return None
        
        # If it's a list and has items, return first one
        if isinstance(self.image_filename, list) and len(self.image_filename) > 0:
            return self.image_filename[0]
        # If it's a string (legacy), return it
        elif isinstance(self.image_filename, str):
            return self.image_filename
        return None

    def get_image_url(self):
        """Get the complete image URL"""
        primary_image = self.get_primary_image()
        if not primary_image:
            return None
        return f"http://127.0.0.1:5000/static/uploads/products/{primary_image}"

    def to_dict(self):
        product = self.product
        
        # Get image URL - try from wishlist item first, then from product
        image_url = self.get_image_url()
        if not image_url and product and product.image_filename:
            # Get primary image from product
            if isinstance(product.image_filename, list) and len(product.image_filename) > 0:
                primary_image = product.image_filename[0]
                image_url = f"http://127.0.0.1:5000/static/uploads/products/{primary_image}"
            elif isinstance(product.image_filename, str) and product.image_filename:
                image_url = f"http://127.0.0.1:5000/static/uploads/products/{product.image_filename}"

        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "title": product.title if product else None,
            "category": product.category if product else None,
            "price": float(product.price) if product else 0,
            "discount": float(product.discount or 0) if product else 0,
            "discounted_price": (
                float(product.discounted_price or product.price or 0)
                if product else 0
            ),
            "reviews": product.reviews if product else 0,
            "stock": product.stock if product else 0,
            "size": product.size if product else None,
            "image_filename": self.get_primary_image() or (product.image_filename[0] if product and isinstance(product.image_filename, list) and len(product.image_filename) > 0 else (product.image_filename if product and isinstance(product.image_filename, str) else None)),
            "previewUrl": image_url,
            "created_at": self.created_at.isoformat()
        }