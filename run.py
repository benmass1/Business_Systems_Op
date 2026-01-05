from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# --- MAANDALIZI YA MFUMO ---
app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_super_secure_key'

# --- DATABASE ENGINE (MAWASILIANO NA SUPABASE) ---
# Kodi hii inasoma siri tano (5) kutoka Vercel Settings
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

# Inatengeneza muundo wa connection string
if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    # Mfumo wa kitaalamu wa Postgres
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    # HII NI SEHEMU YA USALAMA: Ikikosa siri, mfumo utakuambia kosa mapema
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join('/tmp', 'temp_business.db'))

# Marekebisho ya itifaki ya Postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24) # Login inakaa siku nzima

db = SQLAlchemy(app)

# --- MODELS (MEZA ZA DATA) ---
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
    seller_name = db.Column(db.String(50))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")
    admin_password = db.Column(db.String(100), default="1234")

# Kuunda meza zote Supabase
with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings())
            db.session.commit()
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")

# --- ROUTES (NYANJA ZA BIASHARA) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        
        # Admin Backdoor (Kama database ikigoma, tumia hii)
        if u == 'admin' and p == '1234':
            session.update({'logged_in': True, 'role': 'admin', 'username': 'Admin'})
            return redirect(url_for('index'))
            
        # Jaribu watumiaji wa kwenye database
        try:
            user = User.query.filter_by(username=u, password=p).first()
            if user:
                session.update({'logged_in': True, 'role': user.role, 'username': user.username})
                return redirect(url_for('index'))
        except:
            pass # Kama DB haipo, itaangukia kwenye flash hapa chini
            
        flash('Jina la mtumiaji au nambari ya siri si sahihi!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        shop = Settings.query.first()
        products = Product.query.order_by(Product.name.asc()).all()
        
        # Stats Calculation
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_sales = Sale.query.filter(Sale.timestamp >= today_start).all()
        
        total_sales = sum(s.selling_price - s.discount for s in today_sales)
        total_profit = sum(s.profit for s in today_sales)
        total_discount = sum(s.discount for s in today_sales)
        
        return render_template('index.html', products=products, shop=shop, 
                               total_sales=total_sales, total_profit=total_profit, 
                               total_discount=total_discount,
                               low_stock=Product.query.filter(Product.stock <= 5).count())
    except Exception as e:
        return f"DATABASE ERROR: {str(e)}. Angalia siri za Supabase kule Vercel."

# REKEBISHO KUU: Njia ya kuuza bidhaa
@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    try:
        discount = float(request.form.get('discount') or 0)
        if product.stock > 0:
            profit = (product.selling_price - product.buying_price) - discount
            new_sale = Sale(
                product_name=product.name, 
                selling_price=product.selling_price, 
                discount=discount, 
                profit=profit,
                seller_name=session.get('username')
            )
            product.stock -= 1
            db.session.add(new_sale)
            db.session.commit()
            flash(f'Mauzo ya {product.name} yamekamilika!', 'success')
        else:
            flash(f'Bidhaa {product.name} imeisha!', 'warning')
    except:
        db.session.rollback()
        flash('Kosa limetokea wakati wa kuuza.', 'danger')
        
    return redirect(url_for('index'))

@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST' and session.get('role') == 'admin':
        try:
            name = request.form.get('name')
            b_price = float(request.form.get('buying_price'))
            s_price = float(request.form.get('selling_price'))
            stock = int(request.form.get('stock'))
            db.session.add(Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock))
            db.session.commit()
            flash('Bidhaa imesajiliwa!', 'success')
        except: flash('Hakikisha namba ulizoweka ni sahihi!', 'danger')
            
    return render_template('inventory.html', products=Product.query.all())

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        if u and p and not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=p)); db.session.commit()
            flash(f'Muuzaji {u} ameongezwa!', 'success')
    return render_template('staff.html', users=User.query.all())

@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return render_template('sales.html', sales=Sale.query.order_by(Sale.timestamp.desc()).all())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# HANDLING ERROR 405 (METHOD NOT ALLOWED)
@app.errorhandler(405)
def method_not_allowed(e):
    return "KITENDO HAKIRUHUSIWI: Hakikisha fomu yako ya HTML inatumia method='POST'.", 405

if __name__ == '__main__':
    app.run(debug=True)

