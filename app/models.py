from app import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="admin")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    buying_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    stock = db.Column(db.Integer)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
