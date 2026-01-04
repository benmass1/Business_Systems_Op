from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Product, Sale
from app import db

sales = Blueprint('sales', __name__)

@sales.route('/')
@login_required
def dashboard():
    products = Product.query.all()
    total_sales = db.session.query(db.func.sum(Sale.total_price)).scalar() or 0
    return render_template('dashboard.html', products=products, total_sales=total_sales)

@sales.route('/add_product', methods=['POST'])
@login_required
def add_product():
    name = request.form.get('name')
    b_price = float(request.form.get('buying_price'))
    s_price = float(request.form.get('selling_price'))
    stock = int(request.form.get('stock'))
    
    new_product = Product(name=name, buying_price=b_price, selling_price=s_price, stock=stock)
    db.session.add(new_product)
    db.session.commit()
    return redirect(url_for('sales.dashboard'))

@sales.route('/make_sale/<int:p_id>', methods=['POST'])
@login_required
def make_sale(p_id):
    product = Product.query.get(p_id)
    qty = int(request.form.get('qty'))
    if product.stock >= qty:
        total = qty * product.selling_price
        product.stock -= qty
        new_sale = Sale(product_id=p_id, quantity=qty, total_price=total)
        db.session.add(new_sale)
        db.session.commit()
    return redirect(url_for('sales.dashboard'))

