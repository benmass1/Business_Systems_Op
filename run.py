from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# --- INITIALIZATION ---
app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_final_secure_key'

# --- DATABASE ENGINE (SUPABASE CONNECTION) ---
# Inasoma vigezo tano ulizopewa na Supabase
DB_USER = os.getenv("user")
DB_PASS = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port", "5432")
DB_NAME = os.getenv("dbname")

# Inatengeneza daraja la kuelekea Supabase
if all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
else:
    # Ukikosea kuweka siri Vercel, inatumia hii kuzuia duka lisizime
    DATABASE_URL = 'sqlite:///' + os.path.join('/tmp', 'business.db')

# Kurekebisha jina la postgres kwa ajili ya Flask-SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24) # Inakumbuka login kwa siku nzima

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

# Kuunda meza zote Supabase mara ya kwanza
with app.app_context():
    try:
        db.create_all()
        if not Settings.query.first():
            db.session.add(Settings())
            db.session.commit()
    except Exception as e:
        print(f"Connection Error: {e}")

# --- ROUTES (NYANJA ZA MFUMO) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower().strip()
        p = request.form.get('password', '').strip()
        shop = Settings.query.first()
        
        # Admin Backdoor
        if u == 'admin' and p == shop.admin_pass:
            session.permanent = True
            session.update({'logged_in': True, 'role': 'admin', 'user': 'Admin'})
            return redirect(url_for('index'))
            
        # Check registered users in database
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session.permanent = True
            session.update({'logged_in': True, 'role': user.role, 'user': user.username})
            return redirect(url_for('index'))
        
        flash('Jina la mtumiaji au password ni mbaya!', 'danger')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    # Statistics Calculation
    today = datetime.utcnow().date()
    today_sales = Sale.query.filter(db.func.date(Sale.timestamp) == today).all()
    
    stats = {
        'total_sales': sum(s.selling_price - s.discount for s in today_sales),
        'total_profit': sum(s.profit for s in today_sales),
        'total_discount': sum(s.discount for s in today_sales),
        'low_stock': Product.query.filter(Product.stock <= 5).count()
    }
    
    products = Product.query.order_by(Product.name.asc()).all()
    shop = Settings.query.first()
    return render_template('index.html', products=products, stats=stats, shop=shop)

# REKEBISHO KUU: Njia ya kuuza inayokubali POST pekee
@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    product = Product.query.get_or_404(id)
    try:
        discount = float(request.form.get('discount') or 0)
        if product.stock > 0:
            # Hesabu ya faida: (Bei ya kuuza - Bei ya kununua) - Discount
            profit = (product.selling_price - product.buying_price) - discount
            
            new_sale = Sale(
                product_name=product.name,
                selling_price=product.selling_price,
                discount=discount,
                profit=profit,
                seller=session.get('user')
            )
            product.stock -= 1
            db.session.add(new_sale)
            db.session.commit()
            flash(f'Umeuza {product.name} kwa Tsh {product.selling_price - discount}', 'success')
        else:
            flash(f'Bidhaa {product.name} imeisha stoo!', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Kosa limetokea wakati wa kuuza!', 'danger')
        
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
            flash('Bidhaa imeongezwa!', 'success')
        except:
            flash('Kosa! Hakikisha umeingiza namba sahihi.', 'danger')
            
    products = Product.query.all()
    return render_template('inventory.html', products=products)

@app.route('/sales')
def sales():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    all_sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    return render_template('sales.html', sales=all_sales)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').lower().strip()
        password = request.form.get('password')
        if username and password:
            if not User.query.filter_by(username=username).first():
                db.session.add(User(username=username, password=password))
                db.session.commit()
                flash(f'Muuzaji {username} amesajiliwa!', 'success')
            else:
                flash('Huyu muuzaji tayari yupo!', 'warning')
                
    users = User.query.all()
    return render_template('staff.html', users=users)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        shop.shop_name = request.form.get('shop_name')
        new_pass = request.form.get('admin_pass')
        if new_pass: shop.admin_pass = new_pass
        db.session.commit()
        flash('Mipangilio imehifadhiwa!', 'info')
    return render_template('settings.html', shop=shop)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Kuzuia error 405 na 500 kwa weledi
@app.errorhandler(405)
def method_not_allowed(e):
    return "Kitendo hiki hakiruhusiwi. Hakikisha batani ya UZA ipo ndani ya fomu yenye method='POST'.", 405

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return "Kosa la Server! Angalia siri za Supabase kule Vercel.", 500

if __name__ == '__main__':
    app.run(debug=True)

