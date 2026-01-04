
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_key'

# --- DATABASE CONNECTION (Kutumia siri uliyoweka Vercel) ---
uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
elif not uri:
    uri = 'sqlite:///' + os.path.join('/tmp', 'business.db')

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')

with app.app_context():
    db.create_all()
    if not Settings.query.first():
        db.session.add(Settings(shop_name="Business Systems Op"))
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', products=Product.query.all(), shop=Settings.query.first(),
                           total_sales=sum(s.selling_price - s.discount for s in Sale.query.all()),
                           total_profit=sum(s.profit for s in Sale.query.all()),
                           total_discount=sum(s.discount for s in Sale.query.all()),
                           low_stock_count=Product.query.filter(Product.stock <= 5).count())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username').lower().strip()
        p = request.form.get('password').strip()
        if u == 'admin' and p == '1234':
            session['logged_in'], session['role'] = True, 'admin'
            return redirect(url_for('index'))
        user = User.query.filter_by(username=u, password=p).first()
        if user:
            session['logged_in'], session['role'] = True, user.role
            return redirect(url_for('index'))
        flash('Login Imefeli!')
    return render_template('login.html')

# REKEBISHO: Hapa sasa tumeruhusu POST ili uweze ku-add muuzaji
@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username').lower().strip()
        p = request.form.get('password').strip()
        if u and p:
            if not User.query.filter_by(username=u).first():
                db.session.add(User(username=u, password=p))
                db.session.commit()
                flash(f'Muuzaji {u} amesajiliwa!')
            else:
                flash('Jina la muuzaji tayari lipo!')
    return render_template('staff.html', users=User.query.all())

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') == 'admin':
        new_p = Product(name=request.form.get('name'), 
                        buying_price=float(request.form.get('buying_price')),
                        selling_price=float(request.form.get('selling_price')), 
                        stock=int(request.form.get('stock')))
        db.session.add(new_p); db.session.commit()
    return redirect(url_for('index'))

@app.route('/sell/<int:product_id>', methods=['POST'])
def sell_product(product_id):
    p = Product.query.get(product_id)
    discount = float(request.form.get('discount', 0))
    if p and p.stock > 0:
        db.session.add(Sale(product_name=p.name, selling_price=p.selling_price, 
                            discount=discount, profit=(p.selling_price - p.buying_price) - discount))
        p.stock -= 1; db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
