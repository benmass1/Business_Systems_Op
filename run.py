from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# --- MAANDALIZI YA JUU YA MFUMO ---
app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_ultra_final_secret'

# --- USALAMA WA DATABASE (SUPABASE CONNECTION) ---
# Inasoma siri tano (5) kulingana na picha yako ya Supabase
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

# Inatengeneza muundo wa connection kulingana na picha ya Supabase
if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    # Ukikosea siri Vercel, inatumia database ya ndani kuzuia kifo cha duka
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'pos_v10_final.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=48) # Inakumbuka login kwa siku 2
db = SQLAlchemy(app)

# --- MODELS (MEZA ZA DATA - ZIMEBORESHWA) ---
class Product(db.Model):
    __tablename__ = 'pos_products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'pos_sales'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    selling_price = db.Column(db.Float)
    discount = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    seller = db.Column(db.String(50))

class User(db.Model):
    __tablename__ = 'pos_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

class Settings(db.Model):
    __tablename__ = 'pos_settings'
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")
    admin_pass = db.Column(db.String(100), default="1234")

# Kuanzisha database na meza kule Supabase
with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings())
            db.session.commit()
    except Exception as e:
        print(f"DATABASE INITIALIZATION ERROR: {e}")

# --- ROUTES (NYANJA ZOTE ZA MFUMO) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop = Settings.query.first()
        
        # Admin Login
        if u == 'admin' and p == shop.admin_pass:
            session.permanent = True
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
            
        # User Login kule Supabase
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session.permanent = True
            session.update({'logged_in': True, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
        
        flash('Jina la mtumiaji au Password si sahihi!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    # Takwimu za Mauzo (Dashboard Statistics)
    today = datetime.utcnow().date()
    sales = Sale.query.filter(db.func.date(Sale.timestamp) == today).all()
    
    stats = {
        'total_sales': sum(s.selling_price - s.discount for s in sales),
        'total_profit': sum(s.profit for s in sales),
        'total_discount': sum(s.discount for s in sales),
        'low_stock': Product.query.filter(Product.stock <= 5).count()
    }
    
    products = Product.query.order_by(Product.name.asc()).all()
    shop = Settings.query.first()
    return render_template('index.html', products=products, stats=stats, shop=shop)

# REKEBISHO LA KUONGEZA BIDHAA (FULL ADD PRODUCT LOGIC)
@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    try:
        name = request.form.get('product_name')
        b_price = float(request.form.get('buying_price'))
        s_price = float(request.form.get('selling_price'))
        stock = int(request.form.get('stock_quantity'))
        
        if name and b_price and s_price:
            new_item = Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock)
            db.session.add(new_item)
            db.session.commit()
            flash(f'Bidhaa {name} imeongezwa kwenye Stoo!', 'success')
        else:
            flash('Tafadhali jaza taarifa zote kwa usahihi!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'KOSA LA KIUFUNDI: {str(e)}', 'danger')
    return redirect(url_for('inventory'))

# REKEBISHO LA KUUZA BIDHAA (METHOD NOT ALLOWED PROTECTED)
@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    p = Product.query.get_or_404(id)
    try:
        disc = float(request.form.get('discount') or 0)
        if p.stock > 0:
            profit = (p.selling_price - p.buying_price) - disc
            new_sale = Sale(product_name=p.name, selling_price=p.selling_price, 
                            discount=disc, profit=profit, seller=session.get('username'))
            p.stock -= 1
            db.session.commit()
            flash(f'Mauzo ya {p.name} yamekamilika!', 'success')
        else:
            flash(f'Bidhaa {p.name} imeisha!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Kosa wakati wa kuuza: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('inventory.html', products=products)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password')
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=p)); db.session.commit()
            flash(f'Muuzaji {u} ameongezwa!', 'success')
    return render_template('staff.html', users=User.query.all())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name')
        new_pass = request.form.get('admin_pass')
        if new_pass: shop.admin_pass = new_pass
        db.session.commit()
        flash('Mipangilio ya duka imehifadhiwa!', 'success')
    return render_template('settings.html', shop=shop)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ERROR HANDLING ZA KITAALAMU
@app.errorhandler(405)
def method_not_allowed(e):
    return "KOSA 405: Kitendo hiki hakiruhusiwi. Hakikisha fomu inatumia method='POST'.", 405

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return "KOSA LA SERVER (500): Angalia siri za Supabase kule Vercel.", 500

if __name__ == '__main__':
    app.run(debug=True)

