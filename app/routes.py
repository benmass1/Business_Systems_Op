from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Product, User

# Hakikisha jina hapa ni 'main'
main = Blueprint("main", __name__)

@main.route("/")
@login_required
def dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("dashboard.html", products=products)

# Hii ndio route ambayo Flask inaikosa (main.login)
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
            flash("Username au Password siyo sahihi!", "danger")
            
    return render_template("login.html")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Umetoka kwenye mfumo.", "info")
    return redirect(url_for("main.login"))

@main.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name")
        b_price = request.form.get("buying_price")
        s_price = request.form.get("selling_price")
        stock = request.form.get("stock")

        try:
            product = Product(
                name=name,
                buying_price=float(b_price),
                selling_price=float(s_price),
                stock=int(stock)
            )
            db.session.add(product)
            db.session.commit()
            flash(f"Bidhaa {name} imeongezwa! ✅", "success")
            return redirect(url_for("main.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Kuna makosa yamejitokeza.", "danger")

    return render_template("add_product.html")

