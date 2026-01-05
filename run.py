from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# --- MAANDALIZI YA MFUMO ---
app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_super_ultra_key'

# --- DATABASE CONNECTION (SUPABASE) ---
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'pos_v3.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
db = SQLAlchemy(app)

# --- MODELS (MEZA ZA DATA) ---
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
    seller = db.Column(db.String(50))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")
    admin_pass = db.Column(db.String(100), default="1234")

with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings())
            db.session.commit()
    except Exception as e:
        print(f"DB Error: {e}")

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop = Settings.query.first()
        if u == 'admin' and p == shop.admin_pass:
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session.update({'logged_in': True, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
        flash('Login Imefeli!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    shop = Settings.query.first()
    products = Product.query.order_by(Product.name).all()
    today = datetime.utcnow().date()
    sales = Sale.query.filter(db.func.date(Sale.timestamp) == today).all()
    
    t_sales = sum(s.selling_price - s.discount for s in sales)
    t_profit = sum(s.profit for s in sales)
    t_discount = sum(s.discount for s in sales)
    
    return render_template('index.html', products=products, shop=shop, 
                           total_sales=t_sales, total_profit=t_profit, 
                           total_discount=t_discount,
                           low_stock=Product.query.filter(Product.stock <= 5).count())

# REKEBISHO LA KUONGEZA BIDHAA (ADD PRODUCT)
@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    try:
        name = request.form.get('name')
        b_price = float(request.form.get('buying_price'))
        s_price = float(request.form.get('selling_price'))
        stock = int(request.form.get('stock'))
        
        db.session.add(Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock))
        db.session.commit()
        flash(f'Bidhaa {name} imeongezwa!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Kosa! Hakikisha umejaza namba sahihi.', 'danger')
    return redirect(url_for('inventory'))

@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    try:
        disc = float(request.form.get('discount') or 0)
        if p.stock > 0:
            profit = (p.selling_price - p.buying_price) - disc
            db.session.add(Sale(product_name=p.name, selling_price=p.selling_price, 
                                discount=disc, profit=profit, seller=session.get('username')))
            p.stock -= 1
            db.session.commit()
            flash(f'Umeuza {p.name}!', 'success')
        else: flash('Bidhaa imeisha!', 'warning')
    except: flash('Kosa la mauzo!', 'danger')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

# REKEBISHO LA MIPANGILIO (SETTINGS)
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name', shop.shop_name)
        new_pass = request.form.get('admin_pass')
        if new_pass: shop.admin_pass = new_pass
        db.session.commit()
        flash('Mipangilio imesasishwa!', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', shop=shop)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.fdorm.get('password')
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=p)); db.session.commit()
            flash('Muuzaji ameongezwa!', 'success')
    return render_template('staff.html', users=User.query.all())

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

