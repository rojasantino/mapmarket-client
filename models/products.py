from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from db import db
from sqlalchemy import event, text

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller_name = db.Column(db.String(150), nullable=False)

    product_id = db.Column(db.String(50), unique=True, nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    category = db.Column(db.String(100), nullable=False)

    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(5, 2))
    discounted_price = db.Column(db.Numeric(10, 2))

    tax = db.Column(db.Numeric(10, 2))                
    shipping_cost = db.Column(db.Numeric(10, 2))     
    shipping_weight = db.Column(db.Numeric(10, 2))

    features = db.Column(JSON)

    stock = db.Column(db.Integer, nullable=False, default=0)

    material = db.Column(JSON)                       
    size = db.Column(JSON)

    print_quality = db.Column(db.String(100))
    finish = db.Column(db.String(50))

    care_instructions = db.Column(db.Text)

    image_filename = db.Column(JSON, default=[])

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "seller_id": self.seller_id,
            "seller_name": self.seller_name,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "price": float(self.price),
            "tax": float(self.tax or 0),
            "shipping_cost": float(self.shipping_cost or 0),
            "discount": float(self.discount or 0),
            "discounted_price": float(self.discounted_price or self.price),
            "features": self.features,
            "stock": self.stock or 0,
            "material": self.material,
            "size": self.size,
            "print_quality": self.print_quality,
            "finish": self.finish,
            "shipping_weight": float(self.shipping_weight or 0),
            "care_instructions": self.care_instructions,
            "image_filename": self.image_filename,
            "created_at": self.created_at.isoformat()
        }

# ✅ Auto-generate product_id like PRD-001, PRD-002...
@event.listens_for(Product, 'before_insert')
def generate_product_id(mapper, connection, target):
    last_product = connection.execute(
        text("SELECT product_id FROM products ORDER BY id DESC LIMIT 1")
    ).fetchone()
    if last_product and last_product[0]:
        last_num = int(last_product[0].split('-')[1])
        target.product_id = f"PRD-{last_num + 1:03d}"
    else:
        target.product_id = "PRD-001"



