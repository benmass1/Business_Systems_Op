from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_key'

# HAPA NDIPO MUUNGANISHO WA SUPABASE ULIPO
# Inasoma ule mstari ulioweka Vercel (DATABASE_URL)
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
elif not uri:
    # Ikikosa siri, inatumia SQLite ya muda ili duka lisifungwe
    uri = 'sqlite:///' + os.path.join('/tmp', 'business.db')

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS (Zitahifadhiwa Supabase Milele) ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    selling_price = db.Column(db.Float)
    discount = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')

with app.app_context():
    db.create_all() # Hapa duka linatengeneza meza kule Supabase
    if not Settings.query.first():
        db.session.add(Settings(shop_name="Business Systems Op"))
        db.session.commit()

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u_name = request.form.get('username').strip().lower()
        pwd = request.form.get('password').strip()
        if u_name == 'admin' and pwd == '1234':
            session['logged_in'], session['role'], session['username'] = True, 'admin', 'Admin'
            return redirect(url_for('index'))
        if u_name == 'muuzaji' and pwd == '5678':
            session['logged_in'], session['role'], session['username'] = True, 'user', 'Muuzaji'
            return redirect(url_for('index'))
        user = User.query.filter_by(username=u_name, password=pwd).first()
        if user:
            session['logged_in'], session['role'], session['username'] = True, user.role, user.username
            return redirect(url_for('index'))
        flash('Login Imefeli!')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.all()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_sales = Sale.query.filter(Sale.timestamp >= today).all()
    shop = Settings.query.first()
    return render_template('index.html', products=products, shop=shop,
                           total_sales=sum(s.selling_price - s.discount for s in today_sales), 
                           total_profit=sum(s.profit for s in today_sales), 
                           total_discount=sum(s.discount for s in today_sales),
                           low_stock_count=Product.query.filter(Product.stock <= 5).count())

@app.route('/sell/<int:product_id>', methods=['POST'])
def sell_product(product_id):
    p = Product.query.get(product_id)
    discount = float(request.form.get('discount', 0))
    if p and p.stock > 0:
        actual_profit = (p.selling_price - p.buying_price) - discount
        db.session.add(Sale(product_name=p.name, selling_price=p.selling_price, 
                            discount=discount, profit=actual_profit))
        p.stock -= 1; db.session.commit()
        flash(f'Umeuza {p.name}!')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return render_template('sales.html', sales=Sale.query.order_by(Sale.timestamp.desc()).all())

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

