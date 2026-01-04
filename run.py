from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_ultra_secure_key'

# --- USALAMA WA DATABASE (SUPABASE CONNECTION) ---
# Inasoma vigezo vyote vitano ulivyoelekeza kwenye picha ya Supabase
user = os.getenv("user")
password = os.getenv("password")
host = os.getenv("host")
port = os.getenv("port", "5432")
dbname = os.getenv("dbname")

# Inatengeneza muundo wa SQLAlchemy kama kodi yako ya awali
if all([user, password, host, dbname]):
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"
else:
    # Ikikosa siri za Vercel, inatumia DATABASE_URL ya jumla au SQLite ya muda
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'business.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7) # Inakumbuka login kwa wiki nzima
db = SQLAlchemy(app)

# --- MODELS (DATA TABLES) ---
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
    admin_password = db.Column(db.String(100), default="1234")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')

# Kutengeneza meza zote Supabase
with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings(shop_name="Business Systems Op", admin_password="1234"))
            db.session.commit()
    except Exception as e:
        print(f"Database Error: {e}")

# --- MANTIKI YA LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop_set = Settings.query.first()
        
        if u == 'admin' and p == (shop_set.admin_password if shop_set else '1234'):
            session.permanent = True
            session['logged_in'], session['role'], session['username'] = True, 'admin', 'Admin'
            return redirect(url_for('index'))
        
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session.permanent = True
            session['logged_in'], session['role'], session['username'] = True, user.role, user.username
            return redirect(url_for('index'))
        
        flash('Jina la mtumiaji au Password si sahihi!')
    return render_template('login.html')

# --- DASHBOARD (HOME) ---
@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.order_by(Product.name).all()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = Sale.query.filter(Sale.timestamp >= today_start).all()
    shop = Settings.query.first()
    
    return render_template('index.html', 
                           products=products, 
                           shop=shop,
                           total_sales=sum(s.selling_price - s.discount for s in today_sales), 
                           total_profit=sum(s.profit for s in today_sales), 
                           total_discount=sum(s.discount for s in today_sales),
                           low_stock_count=Product.query.filter(Product.stock <= 5).count())

# --- USIMAMIZI WA MAUZO (HAPA NDIPO REKEBISHO LILIPO) ---
@app.route('/sell/<int:product_id>', methods=['POST'])
def sell_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get_or_404(product_id)
    try:
        discount = float(request.form.get('discount') or 0)
        if p.stock > 0:
            actual_profit = (p.selling_price - p.buying_price) - discount
            new_sale = Sale(product_name=p.name, selling_price=p.selling_price, 
                            discount=discount, profit=actual_profit)
            p.stock -= 1
            db.session.add(new_sale)
            db.session.commit()
            flash(f'Mauzo ya {p.name} yamefanikiwa!')
        else:
            flash(f'Bidhaa {p.name} imeisha stoo!')
    except Exception as e:
        db.session.rollback()
        flash('Kosa limetokea wakati wa kuuza.')
    return redirect(url_for('index'))

@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return render_template('sales.html', sales=Sale.query.order_by(Sale.timestamp.desc()).all())

# --- USIMAMIZI WA BIDHAA NA WAFANYAKAZI ---
@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') == 'admin':
        try:
            new_p = Product(name=request.form.get('name'), 
                            buying_price=float(request.form.get('buying_price')),
                            selling_price=float(request.form.get('selling_price')), 
                            stock=int(request.form.get('stock')))
            db.session.add(new_p); db.session.commit()
            flash('Bidhaa imeongezwa!')
        except: flash('Kosa! Angalia namba ulizoweka.')
    return redirect(url_for('index'))

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=p)); db.session.commit()
            flash(f'Muuzaji {u} amesajiliwa vyema!')
    return render_template('staff.html', users=User.query.all())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name', shop.shop_name)
        new_pwd = request.form.get('new_password')
        if new_pwd: shop.admin_password = new_pwd
        db.session.commit()
        flash('Mipangilio imehifadhiwa!')
    return render_template('settings.html', shop=shop)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

