from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db
from app.models import User, Product

# =========================
# BLUEPRINT
# =========================
main = Blueprint("main", __name__)

# =========================
# LOGIN
# =========================
@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Jina au password si sahihi", "danger")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# =========================
# DASHBOARD
# =========================
@main.route("/")
@login_required
def dashboard():
    total_products = Product.query.count()

    # Kwa sasa tunaweka zero (baadaye tutaunganisha sales)
    sales_today = 0
    revenue_today = 0
    profit_today = 0

    return render_template(
        "dashboard.html",
        total_products=total_products,
        sales_today=sales_today,
        revenue_today=revenue_today,
        profit_today=profit_today
    )


# =========================
# ADD PRODUCT
# =========================
@main.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        buy_price = request.form.get("buy_price")
        sell_price = request.form.get("sell_price")
        stock = request.form.get("stock")

        if not name or not buy_price or not sell_price:
            flash("Tafadhali jaza taarifa zote", "danger")
            return redirect(url_for("main.add_product"))

        product = Product(
            name=name,
            buy_price=float(buy_price),
            sell_price=float(sell_price),
            stock=int(stock)
        )

        db.session.add(product)
        db.session.commit()

        flash("Bidhaa imeongezwa kikamilifu", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_product.html")
