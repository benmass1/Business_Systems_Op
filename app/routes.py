from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

# =========================
# BLUEPRINT (LAZIMA IWE JUU)
# =========================
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

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password", "danger")

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
    return render_template(
        "dashboard.html",
        sales_today=0,
        revenue_today=0,
        profit_today=0,
        total_products=0,
        low_stock=0,
        stock_cost=0,
        sales_month=0,
        users_count=1,
        sales_labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        sales_data=[0, 0, 0, 0, 0, 0, 0],
        top_labels=["Sample"],
        top_data=[0]
    )


# =========================
# ADD PRODUCT (GET + POST)
# =========================
@main.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        flash("Product saved successfully (demo mode)", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_product.html")
