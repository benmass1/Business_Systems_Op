from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_key'

# Sehemu ya Database - Salama kwa Vercel
db_path = os.path.join('/tmp', 'business.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
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
    profit = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username').strip().lower()
        pwd = request.form.get('password').strip()
        if user == 'admin' and pwd == '1234':
            session['logged_in'], session['role'] = True, 'admin'
            return redirect(url_for('index'))
        elif user == 'muuzaji' and pwd == '5678':
            session['logged_in'], session['role'] = True, 'user'
            return redirect(url_for('index'))
        flash('Login Failed!')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.all()
    today_sales = Sale.query.filter(Sale.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)).all()
    return render_template('index.html', products=products, 
                           total_sales=sum(s.selling_price for s in today_sales), 
                           total_profit=sum(s.profit for s in today_sales), 
                           low_stock_count=Product.query.filter(Product.stock <= 5).count())

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

# KURASA MPYA ZILIZOKUWA ZINALETA "NOT FOUND"
@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return render_template('sales.html', sales=Sale.query.order_by(Sale.timestamp.desc()).all())

@app.route('/staff')
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return "<h3>Ukurasa wa Wafanyakazi unakuja hivi karibuni...</h3><a href='/'>Rudi</a>"

@app.route('/settings')
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return "<h3>Mipangilio ya Mfumo inakuja hivi karibuni...</h3><a href='/'>Rudi</a>"

@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') == 'admin':
        new_p = Product(name=request.form.get('name'), buying_price=float(request.form.get('buying_price')),
                        selling_price=float(request.form.get('selling_price')), stock=int(request.form.get('stock')))
        db.session.add(new_p); db.session.commit()
    return redirect(url_for('index'))

@app.route('/sell/<int:product_id>')
def sell_product(product_id):
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

