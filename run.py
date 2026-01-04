from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_key'

# Mpangilio wa Database (Vercel Storage Safe)
db_path = os.path.join('/tmp', 'business.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    selling_price = db.Column(db.Float)
    profit = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Inatengeneza Database ikikosekana
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u_name = request.form.get('username').strip().lower()
        pwd = request.form.get('password').strip()
        if u_name == 'admin' and pwd == '1234':
            session['logged_in'], session['role'], session['username'] = True, 'admin', 'Admin'
            return redirect(url_for('index'))
        user = User.query.filter_by(username=u_name, password=pwd).first()
        if user:
            session['logged_in'], session['role'], session['username'] = True, user.role, user.username
            return redirect(url_for('index'))
        flash('Login Failed!')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        products = Product.query.all()
        today = datetime.utcnow().replace(hour=0, minute=0, second=0)
        today_sales = Sale.query.filter(Sale.timestamp >= today).all()
        return render_template('index.html', products=products, 
                               total_sales=sum(s.selling_price for s in today_sales), 
                               total_profit=sum(s.profit for s in today_sales), 
                               low_stock_count=Product.query.filter(Product.stock <= 5).count())
    except:
        return "Shida ya Database! Tafadhali Refresh Page."

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    return render_template('sales.html', sales=sales)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username').lower()
        p = request.form.get('password')
        if u and p:
            db.session.add(User(username=u, password=p)); db.session.commit()
            flash('Muuzaji amesajiliwa!')
    return render_template('staff.html', users=User.query.all())

# HII NDIO ILIKUWA INALETA ERROR KWENYE PICHA YAKO
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        flash('Mipangilio imehifadhiwa!')
        return redirect(url_for('settings'))
    return render_template('settings.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') == 'admin':
        new_p = Product(name=request.form.get('name'), buying_price=float(request.form.get('buying_price')),
                        selling_price=float(request.form.get('selling_price')), stock=int(request.form.get('stock')))
        db.session.add(new_p); db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if session.get('role') == 'admin':
        p = Product.query.get(id)
        if p: db.session.delete(p); db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/sell/<int:product_id>')
def sell_product(product_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    p = Product.query.get(product_id)
    if p and p.stock > 0:
        db.session.add(Sale(product_name=p.name, selling_price=p.selling_price, profit=p.selling_price - p.buying_price))
        p.stock -= 1; db.session.commit()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

