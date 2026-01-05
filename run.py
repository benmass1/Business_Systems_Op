from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func
import os

# --- MAANDALIZI YA MFUMO ---
app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_ultra_secure_v4'

# --- DATABASE CONNECTION (SUPABASE ENHANCED) ---
# Tunachukua siri tano kama ulivyoelekeza kwenye picha za awali
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

# Inatengeneza muundo wa connection kulingana na Supabase SQLAlchemy docs
if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    # Fallback ya usalama kuzuia duka kuzima
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'pos_final_system.db'))

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
db = SQLAlchemy(app)

# --- MODELS (MEZA ZA DATA) ---

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    buying_price = db.Column(db.Float, nullable=False, default=0.0)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    selling_price = db.Column(db.Float)
    discount = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    seller = db.Column(db.String(50))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")
    admin_pass = db.Column(db.String(100), default="1234")
    currency = db.Column(db.String(10), default="Tsh")

# Initialize Tables kule Supabase
with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings())
            db.session.commit()
    except Exception as e:
        print(f"Connection Alert: {e}")

# --- MANTIKI YA USALAMA (DECORATORS) ---
def admin_required():
    if session.get('role') != 'admin':
        flash('Huna ruhusa ya kufanya kitendo hiki!', 'danger')
        return False
    return True

# --- ROUTES (NYANJA ZA BIASHARA) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop = Settings.query.first()
        
        # Admin Backdoor
        if u == 'admin' and p == shop.admin_pass:
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
            
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session.update({'logged_in': True, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
            
        flash('Ingizo si sahihi! Jaribu tena.', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        shop = Settings.query.first()
        products = Product.query.order_by(Product.name).all()
        
        # Takwimu za leo
        today = datetime.utcnow().date()
        sales = Sale.query.filter(func.date(Sale.timestamp) == today).all()
        
        stats = {
            'total_sales': sum(s.selling_price - s.discount for s in sales),
            'total_profit': sum(s.profit for s in sales),
            'total_discount': sum(s.discount for s in sales),
            'low_stock_count': Product.query.filter(Product.stock <= 5).count()
        }
        
        return render_template('index.html', products=products, shop=shop, stats=stats)
    except Exception as e:
        db.session.rollback()
        return f"Database Error: {e}", 500

# --- KIPENGELE CHA KUONGEZA BIDHAA (ENHANCED) ---
@app.route('/add_product', methods=['POST'])
def add_product():
    if not admin_required(): return redirect(url_for('index'))
    try:
        name = request.form.get('name').strip()
        b_price = float(request.form.get('buying_price'))
        s_price = float(request.form.get('selling_price'))
        stock = int(request.form.get('stock'))
        
        if name and b_price >= 0:
            new_p = Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock)
            db.session.add(new_p)
            db.session.commit()
            flash(f'Bidhaa {name} imesajiliwa vyema!', 'success')
        else:
            flash('Tafadhali jaza data sahihi!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Kosa wakati wa kusajili: {str(e)}', 'danger')
    return redirect(url_for('inventory'))

# --- KIPENGELE CHA KUHARIRI BIDHAA (EDIT) ---
@app.route('/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    if not admin_required(): return redirect(url_for('inventory'))
    p = Product.query.get_or_404(id)
    try:
        p.name = request.form.get('name')
        p.buying_price = float(request.form.get('buying_price'))
        p.selling_price = float(request.form.get('selling_price'))
        p.stock = int(request.form.get('stock'))
        db.session.commit()
        flash('Marekebisho yamehifadhiwa!', 'success')
    except:
        db.session.rollback()
        flash('Kosa wakati wa kurekebisha!', 'danger')
    return redirect(url_for('inventory'))

# --- KIPENGELE CHA KUFUTA BIDHAA (DELETE) ---
@app.route('/delete_product/<int:id>')
def delete_product(id):
    if not admin_required(): return redirect(url_for('inventory'))
    p = Product.query.get_or_404(id)
    try:
        db.session.delete(p)
        db.session.commit()
        flash('Bidhaa imefutwa kabisa!', 'info')
    except:
        db.session.rollback()
        flash('Huwezi kufuta bidhaa yenye rekodi za mauzo!', 'danger')
    return redirect(url_for('inventory'))

@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get_or_404(id)
    try:
        disc = float(request.form.get('discount') or 0)
        qty = int(request.form.get('qty', 1)) # Imeongezwa QTY
        
        if p.stock >= qty:
            profit = ((p.selling_price - p.buying_price) * qty) - disc
            new_sale = Sale(
                product_name=p.name, 
                selling_price=p.selling_price * qty, 
                discount=disc, 
                profit=profit, 
                seller=session.get('username')
            )
            p.stock -= qty
            db.session.add(new_sale)
            db.session.commit()
            flash(f'Umeuza {qty} {p.name}!', 'success')
        else:
            flash(f'Stoo haitoshi! Zimebaki {p.stock}', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Kosa la mauzo!', 'danger')
    return redirect(url_for('index'))

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('inventory.html', products=products)

@app.route('/sales')
def sales():
    if not admin_required(): return redirect(url_for('index'))
    all_sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    return render_template('sales.html', sales=all_sales)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not admin_required(): return redirect(url_for('index'))
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
    if not admin_required(): return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password')
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=p))
            db.session.commit()
            flash('Muuzaji mpya ameongezwa!', 'success')
    return render_template('staff.html', users=User.query.all())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

