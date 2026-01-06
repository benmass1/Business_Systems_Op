from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Product, Sale
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

main = Blueprint("main", __name__)

# =========================
# LOGIN
# =========================
@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            # Inampeleka mtumiaji alikotaka kwenda mwanzo (next page)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("main.dashboard"))
        else:
            flash("Username au password si sahihi", "danger")

    return render_template("login.html")

# =========================
# DASHBOARD (FULL LOGIC)
# =========================
@main.route("/")
@login_required
def dashboard():
    today = datetime.utcnow().date()
    
    # 1. Mauzo ya Leo
    sales_today_query = Sale.query.filter(func.date(Sale.created_at) == today).all()
    revenue_today = sum(sale.total_price for sale in sales_today_query)
    profit_today = sum(sale.profit for sale in sales_today_query)
    count_today = len(sales_today_query)

    # 2. Taarifa za Stock
    products = Product.query.all()
    total_products = len(products)
    low_stock = Product.query.filter(Product.stock <= 5).count()
    stock_cost = sum(p.buying_price * p.stock for p in products)

    # 3. Mauzo ya Mwezi huu
    first_day_month = today.replace(day=1)
    sales_month = db.session.query(func.sum(Sale.total_price)).filter(
        Sale.created_at >= first_day_month
    ).scalar() or 0

    # 4. Data za Grafu (Siku 7 zilizopita)
    sales_labels = []
    sales_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        sales_labels.append(day.strftime('%a')) # Mfano: Mon, Tue
        amount = db.session.query(func.sum(Sale.total_price)).filter(
            func.date(Sale.created_at) == day
        ).scalar() or 0
        sales_data.append(amount)

    return render_template(
        "dashboard.html",
        sales_today=count_today,
        revenue_today=revenue_today,
        profit_today=profit_today,
        total_products=total_products,
        low_stock=low_stock,
        stock_cost=stock_cost,
        sales_month=sales_month,
        users_count=User.query.count(),
        sales_labels=sales_labels,
        sales_data=sales_data
    )

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Umetoka kwenye mfumo kwa usalama.", "info")
    return redirect(url_for("main.login"))

