# models/cart.py
from datetime import datetime
from db import db

class Cart(db.Model):
    __tablename__ = "cart"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) 
    product_id = db.Column(db.String(50), db.ForeignKey("products.product_id"), nullable=False)
    product = db.relationship("Product", backref="cart_items", foreign_keys=[product_id])

    title = db.Column(db.String(200), nullable=False)
    size = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(5, 2), nullable=True)
    discounted_price = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, nullable=False, default=0)
    qty = db.Column(db.Integer, nullable=False, default=1)
    shipping_cost = db.Column(db.Numeric(10, 2))
    tax = db.Column(db.Numeric(10, 2))
    total = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Change from String to JSON to match Product model
    image_filename = db.Column(db.JSON, nullable=True)

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
        
        # Get image URL - try from cart item first, then from product
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
            "product_id": product.product_id if product else self.product_id,
            "title": product.title if product else self.title,
            "category": product.category if product else None,
            "price": float(product.price) if product else 0,
            "discount": float(product.discount or 0) if product else 0,
            "discounted_price": float(product.discounted_price or product.price or 0) if product else 0,
            "stock": product.stock if product else self.stock,
            "size": self.size or (product.size if product else None),
            "qty": self.qty,
            "shipping_cost": float(product.shipping_cost or 0) if product else 0,
            "tax": float(product.tax or 0) if product else 0,
            "total": float(self.total),
            "image_filename": self.get_primary_image() or (product.image_filename if product else None),
            "previewUrl": image_url,
            "created_at": self.created_at.isoformat(),
        }