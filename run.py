from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_key'

# Mpangilio wa Database (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'business.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model ya Bidhaa
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

# Model ya Mauzo
class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username').strip().lower()
        pwd = request.form.get('password').strip()
        if user == 'admin' and pwd == '1234':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Login Failed! Tumia admin na 1234')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.all()
    # Mauzo ya leo tu
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_sales = Sale.query.filter(Sale.timestamp >= today_start).all()
    total_sales_val = sum(s.price for s in today_sales)
    low_stock_count = Product.query.filter(Product.stock <= 5).count()
    return render_template('index.html', products=products, total_sales=total_sales_val, low_stock_count=low_stock_count)

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('login'))
    new_p = Product(
        name=request.form.get('name'),
        buying_price=float(request.form.get('buying_price')),
        selling_price=float(request.form.get('selling_price')),
        stock=int(request.form.get('stock'))
    )
    db.session.add(new_p)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/sell/<int:product_id>')
def sell_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get(product_id)
    if p and p.stock > 0:
        p.stock -= 1
        new_sale = Sale(product_name=p.name, price=p.selling_price)
        db.session.add(new_sale)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

