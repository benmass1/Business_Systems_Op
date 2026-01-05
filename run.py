from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_stable_v5'

# --- DATABASE CONNECTION (SUPABASE) ---
# Inasoma siri tano (5) kutoka Vercel Settings
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

# Inatengeneza muundo wa connection
if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    # Fallback ya usalama
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'pos_stable.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
db = SQLAlchemy(app)

# --- MODELS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False, default=0.0)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)

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
        print(f"Connection Alert: {e}")

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop = Settings.query.first()
        
        # Admin Backdoor
        if u == 'admin' and p == (shop.admin_pass if shop else '1234'):
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
            
        try:
            user = User.query.filter_by(username=u, password=p).first()
            if user:
                session.update({'logged_in': True, 'role': user.role, 'username': user.username})
                return redirect(url_for('index'))
        except: pass
        
        flash('Jina la mtumiaji au password si sahihi!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        shop = Settings.query.first()
        products = Product.query.order_by(Product.name).all()
        
        # Statistics (Leo Pekee)
        today = datetime.utcnow().date()
        all_sales = Sale.query.all()
        today_sales = [s for s in all_sales if s.timestamp.date() == today]
        
        stats = {
            'total_sales': sum(s.selling_price - s.discount for s in today_sales),
            'total_profit': sum(s.profit for s in today_sales),
            'total_discount': sum(s.discount for s in today_sales),
            'low_stock': Product.query.filter(Product.stock <= 5).count()
        }
        
        return render_template('index.html', products=products, shop=shop, stats=stats)
    except Exception as e:
        return f"Database Error: {str(e)}"

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
        flash('Bidhaa imeongezwa!', 'success')
    except:
        db.session.rollback()
        flash('Kosa la data!', 'danger')
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
            flash('Umeuza!', 'success')
        else: flash('Stoo imeisha!', 'warning')
    except:
        db.session.rollback()
        flash('Kosa!', 'danger')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name')
        new_p = request.form.get('admin_pass')
        if new_p: shop.admin_pass = new_p
        db.session.commit()
        flash('Imehifadhiwa!', 'success')
    return render_template('settings.html', shop=shop)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

