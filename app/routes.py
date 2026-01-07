herefrom flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import User, Product, Sale
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

main = Blueprint("main", __name__)

@main.route("/")
@login_required
def dashboard():
    try:
        today = datetime.utcnow().date()
        
        # 1. Analytics - Tumia 0 kama hakuna mauzo
        sales_today = Sale.query.filter(func.date(Sale.created_at) == today).all()
        revenue = sum(s.total_price for s in sales_today) if sales_today else 0
        profit = sum(s.profit for s in sales_today) if sales_today else 0
        
        # 2. Stock Alerts
        low_stock_count = Product.query.filter(Product.stock <= 5).count()
        all_products = Product.query.order_by(Product.name.asc()).all()
        
        # 3. Recent Sales
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()

        # 4. Graph Data
        labels = []
        data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime('%a'))
            val = db.session.query(func.sum(Sale.total_price)).filter(func.date(Sale.created_at) == day).scalar()
            data.append(float(val) if val else 0.0)

        return render_template(
            "dashboard.html", 
            revenue=revenue, 
            profit=profit, 
            low_stock=low_stock_count, 
            total_products=len(all_products),
            all_products=all_products,
            recent_sales=recent_sales,
            labels=labels, 
            data=data
        )
    except Exception as e:
        db.session.rollback()
        # Hii itakuonyesha kosa halisi kwenye terminal/log
        print(f"DEBUG ERROR: {e}")
        return f"Tatizo la Mfumo: {e}. Jaribu kufuta business.db na uwashe upya."

@main.route("/sell", methods=["POST"])
@login_required
def sell_product():
    try:
        p_id = request.form.get("product_id")
        qty_val = request.form.get("quantity")

        if not p_id or not qty_val:
            flash("Ingiza bidhaa na idadi!", "warning")
            return redirect(url_for("main.dashboard"))

        product = Product.query.get(int(p_id))
        qty = int(qty_val)

        if product and product.stock >= qty:
            total = product.selling_price * qty
            gain = (product.selling_price - product.buying_price) * qty
            
            new_sale = Sale(
                product_id=product.id,
                user_id=current_user.id,
                quantity=qty,
                selling_price=product.selling_price,
                total_price=total,
                profit=gain
            )
            
            product.stock -= qty
            db.session.add(new_sale)
            db.session.commit()
            flash(f"✅ Umeuza {product.name}!", "success")
        else:
            flash("❌ Stock haitoshi!", "danger")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Kosa: {e}", "danger")
        
    return redirect(url_for("main.dashboard"))
