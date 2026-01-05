from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_super_key'

# --- DATABASE SETUP (SUPABASE & SQLITE FALLBACK) ---
user = os.getenv("user")
password = os.getenv("password")
host = os.getenv("host")
port = os.getenv("port", "5432")
dbname = os.getenv("dbname")

# Inatengeneza muundo wa SQLAlchemy kama kodi yako
if all([user, password, host, dbname]):
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
else:
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'business.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")

with app.app_context():
    db.create_all()
    if not Settings.query.first():
        db.session.add(Settings(shop_name="Business Systems Op"))
        db.session.commit()

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        if u == 'admin' and p == '1234':
            session.permanent = True
            session['logged_in'], session['role'], session['username'] = True, 'admin', 'Admin'
            return redirect(url_for('index'))
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session['logged_in'], session['role'], session['username'] = True, user.role, user.username
            return redirect(url_for('index'))
        flash('Login Imefeli!')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.order_by(Product.name).all()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    sales = Sale.query.filter(Sale.timestamp >= today).all()
    return render_template('index.html', products=products, shop=Settings.query.first(),
                           total_sales=sum(s.selling_price - s.discount for s in sales),
                           total_profit=sum(s.profit for s in sales),
                           total_discount=sum(s.discount for s in sales),
                           low_stock=Product.query.filter(Product.stock <= 5).count())

# HAPA NDIPO REKEBISHO LA "METHOD NOT ALLOWED" LILIPO
@app.route('/sell/<int:id>', methods=['GET', 'POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    if request.method == 'POST':
        disc = float(request.form.get('discount') or 0)
        if p.stock > 0:
            profit = (p.selling_price - p.buying_price) - disc
            db.session.add(Sale(product_name=p.name, selling_price=p.selling_price, discount=disc, profit=profit))
            p.stock -= 1
            db.session.commit()
            flash(f'Umeuza {p.name}!')
        else:
            flash('Stoo imeisha!')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') == 'admin':
        db.session.add(Product(name=request.form.get('name'), 
                               buying_price=float(request.form.get('buying_price')),
                               selling_price=float(request.form.get('selling_price')), 
                               stock=int(request.form.get('stock'))))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u.lower(), password=p)); db.session.commit()
    return render_template('staff.html', users=User.query.all())

@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return render_template('sales.html', sales=Sale.query.order_by(Sale.timestamp.desc()).all())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    s = Settings.query.first()
    if request.method == 'POST':
        s.shop_name = request.form.get('shop_name'); db.session.commit()
    return render_template('settings.html', shop=s)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

