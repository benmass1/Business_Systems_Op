from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Product, Sale
from app import db
from sqlalchemy import func

sales = Blueprint('sales', __name__)

@sales.route('/')
@login_required
def dashboard():
    products = Product.query.all()
    total_sales = db.session.query(func.sum(Sale.total_price)).scalar() or 0
    return render_template(
        'dashboard.html',
        products=products,
        total_sales=total_sales
    )

@sales.route('/add_product', methods=['POST'])
@login_required
def add_product():
    name = request.form.get('name')
    price = float(request.form.get('price'))
    stock = int(request.form.get('stock'))

    product = Product(name=name, price=price, stock=stock)
    db.session.add(product)
    db.session.commit()

    flash("Bidhaa imeongezwa", "success")
    return redirect(url_for('sales.dashboard'))

@sales.route('/make_sale/<int:product_id>', methods=['POST'])
@login_required
def make_sale(product_id):
    product = Product.query.get_or_404(product_id)
    qty = int(request.form.get('qty'))

    if product.stock < qty:
        flash("Stock haitoshi", "danger")
        return redirect(url_for('sales.dashboard'))

    total = qty * product.price
    product.stock -= qty

    sale = Sale(
        product_id=product.id,
        quantity=qty,
        total_price=total
    )

    db.session.add(sale)
    db.session.commit()

    flash("Mauzo yamefanikiwa", "success")
    return redirect(url_for('sales.dashboard'))
