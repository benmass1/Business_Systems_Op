from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os

# ---------------- BASIC SETUP ----------------
app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_master_key_v10'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- DATABASE CONFIG (SUPABASE) ----------------
# Inasoma siri kutoka Vercel kuzuia kosa la connection
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    # Ukikosea siri, inatumia database ya ndani kuzuia mfumo kuzima
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'pos_final_stable.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- MODELS ----------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    selling_price = db.Column(db.Float)
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
    shop_slogan = db.Column(db.String(200), default="Huduma Bora")
    admin_password = db.Column(db.String(200), default=generate_password_hash("1234"))

# 

# ---------------- INITIALIZE DB ----------------
with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings())
            db.session.commit()
    except Exception as e:
        logging.error(f"DATABASE ERROR: {e}")

# ---------------- AUTH ----------------
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- DASHBOARD ----------------
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        shop = Settings.query.first()
        products = Product.query.order_by(Product.name.asc()).all()
        today = datetime.utcnow().date()
        sales_today = Sale.query.filter(db.func.date(Sale.timestamp) == today).all()

        return render_template(
            'index.html',
            shop=shop,
            products=products,
            total_sales=sum(s.selling_price - s.discount for s in sales_today),
            total_profit=sum(s.profit for s in sales_today),
            total_discount=sum(s.discount for s in sales_today),
            low_stock=Product.query.filter(Product.stock <= 5).count()
        )
    except Exception as e:
        logging.error(e)
        return "KOSA LA DATABASE: Angalia Environment Variables kule Vercel."

# ---------------- PRODUCTS ----------------
@app.route('/inventory')
def inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('inventory.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    try:
        name = request.form.get('name')
        b_price = float(request.form.get('buying_price') or 0)
        s_price = float(request.form.get('selling_price') or 0)
        stock = int(request.form.get('stock') or 0)

        if not name:
            flash('Jina la bidhaa ni lazima!', 'warning')
            return redirect(url_for('inventory'))

        db.session.add(Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock))
        db.session.commit()
        flash(f'Bidhaa {name} imesajiliwa!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Kosa! Hakikisha umejaza namba sahihi.', 'danger')
    return redirect(url_for('inventory'))

# ---------------- SELL (PROTECTED POST METHOD) ----------------
@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    try:
        disc = float(request.form.get('discount') or 0)
        if disc < 0 or disc > p.selling_price:
            flash('Discount si sahihi!', 'warning')
            return redirect(url_for('index'))
        if p.stock <= 0:
            flash(f'Bidhaa {p.name} imeisha!', 'warning')
            return redirect(url_for('index'))

        profit = (p.selling_price - p.buying_price) - disc
        db.session.add(Sale(
            product_name=p.name,
            selling_price=p.selling_price,
            discount=disc,
            profit=max(profit, 0),
            seller_name=session.get('username')
        ))
        p.stock -= 1
        db.session.commit()
        flash(f'Umeuza {p.name}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Kosa la mauzo!', 'danger')
    return redirect(url_for('index'))

# ---------------- SALES REPORT (REKEBISHO KUU) ----------------
@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    try:
        sales = Sale.query.order_by(Sale.timestamp.desc()).all()
        # Lazima tuitume stats ili HTML isizime
        stats = {
            'total_sales_month': sum(s.selling_price - s.discount for s in sales),
            'total_profit_month': sum(s.profit for s in sales),
            'total_sales_today': sum(s.selling_price - s.discount for s in sales if s.timestamp.date() == datetime.utcnow().date()),
            'total_count': len(sales)
        }
        return render_template('sales.html', sales=sales, stats=stats)
    except Exception as e:
        logging.error(e)
        return "Internal Server Error: Ripoti imeshindwa kufunguka.", 500

# ---------------- SETTINGS ----------------
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name', shop.shop_name)
        shop.shop_slogan = request.form.get('shop_slogan', shop.shop_slogan)
        curr = request.form.get('current_password')
        new = request.form.get('new_password')
        conf = request.form.get('confirm_password')

        if curr and check_password_hash(shop.admin_password, curr):
            if new and new == conf and len(new) >= 6:
                shop.admin_password = generate_password_hash(new)
                flash('Password imesasishwa!', 'success')
            db.session.commit()
            flash('Mipangilio imehifadhiwa!', 'success')
        else:
            flash('Password ya sasa si sahihi!', 'danger')
        return redirect(url_for('settings'))
    return render_template('settings.html', shop=shop)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=generate_password_hash(p)))
            db.session.commit()
            flash(f'Muuzaji {u} ameongezwa!', 'success')
    return render_template('staff.html', users=User.query.all())

if __name__ == '__main__':
    app.run(debug=True)

