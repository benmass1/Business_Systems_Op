from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import User, Product, Sale
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

main = Blueprint("main", __name__)

@main.route("/")
@login_required
def dashboard():
    # 1. Dashboard Analytics & 8. Visual Reports
    today = datetime.utcnow().date()
    sales_today = Sale.query.filter(func.date(Sale.created_at) == today).all()
    
    revenue = sum(s.total_price for s in sales_today)
    profit = sum(s.profit for s in sales_today)
    
    # 4. Stock Alerts
    low_stock = Product.query.filter(Product.stock <= 5).all()
    
    # Data za Grafu
    labels = [(today - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
    data = [db.session.query(func.sum(Sale.total_price)).filter(func.date(Sale.created_at) == (today - timedelta(days=i))).scalar() or 0 for i in range(6, -1, -1)]

    return render_template("dashboard.html", revenue=revenue, profit=profit, 
                           low_stock=len(low_stock), total_products=Product.query.count(),
                           labels=labels, data=data)

# 2. Point of Sale (POS)
@main.route("/sell", methods=["POST"])
@login_required
def sell_product():
    p_id = request.form.get("product_id")
    qty = int(request.form.get("quantity"))
    product = Product.query.get(p_id)

    if product and product.stock >= qty:
        total = product.selling_price * qty
        # 6. Profit Tracking (Selling - Buying)
        gain = (product.selling_price - product.buying_price) * qty
        
        new_sale = Sale(product_id=p_id, user_id=current_user.id, 
                        quantity=qty, total_price=total, profit=gain)
        product.stock -= qty # Punguza Stock
        db.session.add(new_sale)
        db.session.commit()
        flash(f"Umeuza {product.name} kwa Tsh {total}", "success")
    else:
        flash("Stock haitoshi!", "danger")
    return redirect(url_for("main.dashboard"))

