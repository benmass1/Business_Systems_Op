herefrom datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# =========================
# USER MODEL
# =========================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    # Tumesajili kama 'password_hash' badala ya 'password' kwa usalama
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="admin")  # admin / staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Uhusiano na mauzo (kujua nani aliuza nini)
    sales_made = db.relationship("Sale", backref="seller", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# PRODUCT MODEL
# =========================
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sales = db.relationship("Sale", backref="product", lazy=True)
    stock_movements = db.relationship("StockMovement", backref="product", lazy=True)

    @property
    def unit_profit(self):
        return self.selling_price - self.buying_price

    def __repr__(self):
        return f"<Product {self.name}>"

# =========================
# SALE MODEL
# =========================
class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False) # Bei wakati wa kuuza
    total_price = db.Column(db.Float, nullable=False)
    
    # Faida ya mauzo haya (Total Price - (Buying Price * Qty))
    profit = db.Column(db.Float, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Sale ProductID={self.product_id} Total={self.total_price}>"

# =========================
# STOCK MOVEMENT MODEL
# =========================
class StockMovement(db.Model):
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(50))  # IN / OUT
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Stock {self.movement_type} {self.quantity}>"
