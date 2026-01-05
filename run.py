from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
import os
import logging

# --- CONFIGURATION & LOGGING ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'business_systems_op_ultra_2026_key')
logging.basicConfig(level=logging.INFO)

# --- DATABASE SETUP (SUPABASE ENHANCED) ---
# Tunatumia vigezo vyote ulivyopewa na Supabase kuzuia error za connection
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port", "5432")
DBNAME = os.getenv("dbname")

if all([USER, PASSWORD, HOST, DBNAME]):
    # Mfumo wa Postgres kwa ajili ya Supabase
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
else:
    # Fallback ya usalama ikikosa siri za Vercel
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'business.db'))

# Marekebisho ya itifaki ya Postgres kwa ajili ya SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12) # Login inakaa muda mrefu

db = SQLAlchemy(app)

# --- DATABASE MODELS (MISTARI 300+ STRUCTURE) ---

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    buying_price = db.Column(db.Float, nullable=False, default=0.0)
    selling_price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "stock": self.stock}

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name = db.Column(db.String(100))
    selling_price = db.Column(db.Float)
    discount = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float)
    seller_name = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin' au 'user'

class ShopSettings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")
    currency = db.Column(db.String(10), default="Tsh")
    low_stock_threshold = db.Column(db.Integer, default=5)

# Initialize Tables
with app.app_context():
    try:
        db.create_all()
        if not ShopSettings.query.first():
            db.session.add(ShopSettings())
            db.session.commit()
    except Exception as e:
        logging.error(f"Initialization Error: {e}")

# --- HELPER FUNCTIONS (ERROR PROTECTION) ---

def get_shop_data():
    return ShopSettings.query.first()

def is_admin():
    return session.get('role') == 'admin'

# --- ROUTES (FULL FEATURED) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').lower().strip()
        password = request.form.get('password', '').strip()
        
        # Hardcoded Admin for Emergency
        if username == 'admin' and password == '1234':
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
            
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session.update({'logged_in': True, 'role': user.role, 'username': user.username})
            return redirect(url_for('index'))
            
        flash('Jina la mtumiaji au password si sahihi!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        shop = get_shop_data()
        products = Product.query.order_by(Product.name).all()
        
        # Statistics Logic
        today = datetime.utcnow().date()
        sales_today = Sale.query.filter(db.func.date(Sale.timestamp) == today).all()
        
        stats = {
            'total_sales': sum((s.selling_price - s.discount) for s in sales_today),
            'total_profit': sum(s.profit for s in sales_today),
            'total_discount': sum(s.discount for s in sales_today),
            'low_stock_count': Product.query.filter(Product.stock <= shop.low_stock_threshold).count()
        }
        
        return render_template('index.html', products=products, stats=stats, shop=shop)
    except SQLAlchemyError as e:
        db.session.rollback()
        return "Database Error: Hakikisha Supabase imeunganishwa vizuri.", 500

@app.route('/sell/<int:product_id>', methods=['POST'])
def sell_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        # Pata bidhaa na kuzuia error ya kutopatikana
        product = Product.query.get_or_404(product_id)
        discount = float(request.form.get('discount') or 0)
        
        if product.stock <= 0:
            flash(f'Samahani, {product.name} imeisha stoo!', 'warning')
            return redirect(url_for('index'))
            
        # Calculation ya faida
        profit = (product.selling_price - product.buying_price) - discount
        
        # Record Sale
        new_sale = Sale(
            product_id=product.id,
            product_name=product.name,
            selling_price=product.selling_price,
            discount=discount,
            profit=profit,
            seller_name=session.get('username')
        )
        
        # Update Stock
        product.stock -= 1
        
        db.session.add(new_sale)
        db.session.commit()
        flash(f'Umeuza {product.name} kwa mafanikio!', 'success')
        
    except ValueError:
        flash('Kosa: Tafadhali weka namba sahihi kwenye punguzo.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('Kosa la mfumo limetokea. Jaribu tena.', 'danger')
        
    return redirect(url_for('index'))

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST' and is_admin():
        try:
            name = request.form.get('name')
            b_price = float(request.form.get('buying_price'))
            s_price = float(request.form.get('selling_price'))
            stock = int(request.form.get('stock'))
            
            new_prod = Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock)
            db.session.add(new_prod)
            db.session.commit()
            flash('Bidhaa imeongezwa!', 'success')
        except:
            flash('Kosa wakati wa kuongeza bidhaa!', 'danger')
            
    products = Product.query.all()
    return render_template('inventory.html', products=products)

@app.route('/sales')
def sales_report():
    if not is_admin(): return redirect(url_for('index'))
    # Panga mauzo kuanzia mapya zaidi
    sales = Sale.query.order_by(Sale.timestamp.desc()).limit(500).all()
    return render_template('sales.html', sales=sales)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if not is_admin(): return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = request.form.get('username').lower().strip()
        pwd = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if user and pwd:
            if not User.query.filter_by(username=user).first():
                db.session.add(User(username=user, password=pwd, role=role))
                db.session.commit()
                flash('Mtumiaji amesajiliwa!', 'success')
            else:
                flash('Jina hili tayari lipo!', 'warning')
                
    users = User.query.all()
    return render_template('staff.html', users=users)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not is_admin(): return redirect(url_for('index'))
    shop = get_shop_data()
    
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name', shop.shop_name)
        shop.low_stock_threshold = int(request.form.get('threshold', 5))
        db.session.commit()
        flash('Mipangilio imehifadhiwa!', 'info')
        
    return render_template('settings.html', shop=shop)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ERROR HANDLERS (KUZUIA "METHOD NOT ALLOWED" NA NYINGINE) ---

@app.errorhandler(404)
def not_found(e):
    return "Ukurasa haupatikani!", 404

@app.errorhandler(405)
def method_not_allowed(e):
    return "Kitendo hiki hakiruhusiwi (Method Not Allowed). Hakikisha fomu yako inatumia POST.", 405

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return "Kosa la ndani la server! Angalia kama Supabase imezidiwa au kodi ina makosa.", 500

if __name__ == '__main__':
    app.run(debug=True)

