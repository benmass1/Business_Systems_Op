import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'masanja_business_key_2026'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# DATABASE CONFIG: Kutumia folder la /tmp kuzuia crash Vercel
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join('/tmp', 'duka.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# MODELS
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float)
    discount = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    seller_name = db.Column(db.String(50))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")
    admin_password = db.Column(db.String(200), default=generate_password_hash("1234"))

# INITIALIZE DATABASE: Hii itaunda kila kitu bila kuhitaji SQL Editor
with app.app_context():
    db.create_all()
    if not Settings.query.first():
        db.session.add(Settings())
        db.session.commit()

# ROUTES
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop = Settings.query.first()
        if u == 'admin' and shop and check_password_hash(shop.admin_password, p):
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session.update({'logged_in': True, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
        flash('Jina la mtumiaji au password si sahihi!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    shop = Settings.query.first()
    products = Product.query.order_by(Product.name.asc()).all()
    today = datetime.utcnow().date()
    sales_today = Sale.query.filter(db.func.date(Sale.timestamp) == today).all()
    return render_template('index.html', shop=shop, products=products, 
                           total_sales=sum(s.total_price - s.discount for s in sales_today),
                           total_profit=sum(s.profit for s in sales_today),
                           low_stock=Product.query.filter(Product.stock <= 5).count(),
                           datetime_now=datetime.now().strftime("%Y-%m-%d %H:%M"))

@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    try:
        qty = int(request.form.get('quantity') or 1)
        disc = float(request.form.get('discount') or 0)
        if p.stock >= qty:
            t_price = p.selling_price * qty
            profit = (t_price - (p.buying_price * qty)) - disc
            db.session.add(Sale(product_name=p.name, quantity=qty, total_price=t_price, 
                                discount=disc, profit=max(profit,0), seller_name=session.get('username')))
            p.stock -= qty
            db.session.commit()
            flash(f'Umeuza {p.name}!', 'success')
        else: flash('Mzigo hautoshi!', 'warning')
    except: db.session.rollback()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

