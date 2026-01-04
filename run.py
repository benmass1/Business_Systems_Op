from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'business_systems_op_2026_key'

# Database Setup
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

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default="Business Systems Op")

with app.app_context():
    db.create_all()
    if not Settings.query.first():
        db.session.add(Settings(shop_name="Business Systems Op"))
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u_name = request.form.get('username').strip().lower()
        pwd = request.form.get('password').strip()
        
        # 1. LOGIN ZA KUDUMU (Hizi hazitakataa kamwe)
        # Admin wa kudumu
        if u_name == 'admin' and pwd == '1234':
            session['logged_in'], session['role'], session['username'] = True, 'admin', 'Admin'
            return redirect(url_for('index'))
        
        # Muuzaji wa kudumu (Tumia hii kama Database ikizingua)
        if u_name == 'muuzaji' and pwd == '5678':
            session['logged_in'], session['role'], session['username'] = True, 'user', 'Muuzaji'
            return redirect(url_for('index'))
        
        # 2. LOGIN KUTOKA KWENYE DATABASE (Wale unaosajili)
        user = User.query.filter_by(username=u_name, password=pwd).first()
        if user:
            session['logged_in'], session['role'], session['username'] = True, user.role, user.username
            return redirect(url_for('index'))
        
        flash('Jina au Password siyo sahihi! Jaribu kutumia muuzaji/5678')
    return render_template('login.html')

@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    products = Product.query.all()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_sales = Sale.query.filter(Sale.timestamp >= today).all()
    shop = Settings.query.first()
    return render_template('index.html', products=products, shop=shop,
                           total_sales=sum(s.selling_price for s in today_sales), 
                           total_profit=sum(s.profit for s in today_sales), 
                           low_stock_count=Product.query.filter(Product.stock <= 5).count())

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        u = request.form.get('username').strip().lower()
        p = request.form.get('password').strip()
        if u and p:
            # Hakikisha mtumiaji hayupo tayari
            if not User.query.filter_by(username=u).first():
                db.session.add(User(username=u, password=p))
                db.session.commit()
                flash(f'Muuzaji {u} amesajiliwa!')
            else:
                flash('Jina hili tayari lipo!')
    return render_template('staff.html', users=User.query.all())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    shop = Settings.query.first()
    if request.method == 'POST':
        new_name = request.form.get('shop_name')
        if new_name: 
            shop.shop_name = new_name
            db.session.commit()
        flash('Mipangilio imehifadhiwa!')
        return redirect(url_for('settings'))
    return render_template('settings.html', shop=shop)

@app.route('/inventory')
def inventory():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('inventory.html', products=Product.query.all())

@app.route('/sales')
def sales_report():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    return render_template('sales.html', sales=Sale.query.order_by(Sale.timestamp.desc()).all())

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
