from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Product, Sale
from app import db
from sqlalchemy import func

sales = Blueprint('sales', __name__, url_prefix="/sales")

# ======================
# DASHBOARD
# ======================
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

# ======================
# ADD PRODUCT
# ======================
@sales.route('/add_product', methods=['POST'])
@login_required
def add_product():
    try:
        name = request.form.get('name')
        buying_price = float(request.form.get('buying_price'))
        selling_price = float(request.form.get('selling_price'))
        stock = int(request.form.get('stock'))

        if not name or buying_price <= 0 or selling_price <= 0 or stock < 0:
            flash("Tafadhali jaza taarifa sahihi", "danger")
            return redirect(url_for('sales.dashboard'))

        product = Product(
            name=name,
            buying_price=buying_price,
            selling_price=selling_price,
            stock=stock
        )

        db.session.add(product)
        db.session.commit()
        flash("Bidhaa imeongezwa kikamilifu", "success")

    except Exception as e:
        db.session.rollback()
        flash("Kuna kosa limejitokeza", "danger")

    return redirect(url_for('sales.dashboard'))

# ======================
# MAKE SALE
# ======================
@sales.route('/make_sale/<int:product_id>', methods=['POST'])
@login_required
def make_sale(product_id):
    product = Product.query.get_or_404(product_id)

    try:
        quantity = int(request.form.get('qty'))

        if quantity <= 0:
            flash("Idadi sio sahihi", "danger")
            return redirect(url_for('sales.dashboard'))

        if product.stock < quantity:
            flash("Stock haitoshi", "warning")
            return redirect(url_for('sales.dashboard'))

        total = quantity * product.selling_price

        sale = Sale(
            product_id=product.id,
            quantity=quantity,
            total_price=total
        )

        product.stock -= quantity

        db.session.add(sale)
        db.session.commit()
        flash("Mauzo yamefanikiwa", "success")

    except Exception:
        db.session.rollback()
        flash("Kosa limetokea wakati wa kuuza", "danger")

    return redirect(url_for('sales.dashboard'))
