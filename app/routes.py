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
    try:
        today = datetime.utcnow().date()
        
        # 1. Dashboard Analytics
        sales_today = Sale.query.filter(func.date(Sale.created_at) == today).all()
        revenue = sum(s.total_price for s in sales_today)
        profit = sum(s.profit for s in sales_today)
        
        # 4. Stock Alerts (Bidhaa zenye stock chini ya 5)
        low_stock_count = Product.query.filter(Product.stock <= 5).count()
        
        # 3. Inventory Management & 2. POS Data
        # Hapa ndipo palikuwa na kosa - lazima tupitishe all_products
        all_products = Product.query.order_by(Product.name).all()
        
        # 5. Sales History (Mauzo 10 ya mwisho)
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()

        # 8. Visual Reports (Data za Grafu ya Siku 7)
        labels = []
        data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime('%a'))
            # Query salama zaidi kwa mifumo yote ya database
            daily_total = db.session.query(func.sum(Sale.total_price)).filter(
                func.date(Sale.created_at) == day
            ).scalar() or 0
            data.append(float(daily_total))

        return render_template(
            "dashboard.html", 
            revenue=revenue, 
            profit=profit, 
            low_stock=low_stock_count, 
            total_products=len(all_products),
            all_products=all_products, # Hii ni muhimu kwa POS dropdown
            recent_sales=recent_sales, # Feature: Sales History
            labels=labels, 
            data=data
        )
    except Exception as e:
        print(f"Error: {e}")
        return "Kuna tatizo kwenye Database. Hakikisha umerun migrations/db.create_all()"

@main.route("/sell", methods=["POST"])
@login_required
def sell_product():
    p_id = request.form.get("product_id")
    qty_str = request.form.get("quantity")

    if not p_id or not qty_str:
        flash("Tafadhali jaza bidhaa na idadi", "warning")
        return redirect(url_for("main.dashboard"))

    qty = int(qty_str)
    product = Product.query.get(p_id)

    if product and product.stock >= qty:
        total = product.selling_price * qty
        # 6. Profit Tracking
        gain = (product.selling_price - product.buying_price) * qty
        
        new_sale = Sale(
            product_id=p_id, 
            user_id=current_user.id, 
            quantity=qty, 
            total_price=total, 
            profit=gain,
            selling_price=product.selling_price # Tunahifadhi bei ya wakati huo
        )
        
        product.stock -= qty 
        db.session.add(new_sale)
        db.session.commit()
        flash(f"✅ Umeuza {product.name} (Qty: {qty}) kwa Tsh {total:,.0f}", "success")
    else:
        flash("❌ Stock haitoshi au bidhaa haipo!", "danger")
        
    return redirect(url_for("main.dashboard"))
