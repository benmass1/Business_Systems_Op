from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from app.models import User, Product, Sale
from app import db, login_manager

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()
        if user:
            login_user(user)
            return redirect(url_for("main.dashboard"))
    return render_template("login.html")

@main.route("/dashboard")
@login_required
def dashboard():
    products = Product.query.all()
    sales = Sale.query.all()
    return render_template("dashboard.html", products=products, sales=sales)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))
