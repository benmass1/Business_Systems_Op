from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required
from app import db
from app.models import Product

main = Blueprint("main", __name__)

@main.route("/")
@login_required
def dashboard():
    # Tunachukua bidhaa zote zilizopangwa kwa tarehe
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("dashboard.html", products=products)

@main.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        # Kuchukua data kutoka kwenye form
        name = request.form.get("name", "").strip()
        buying_price = request.form.get("buying_price")
        selling_price = request.form.get("selling_price")
        stock = request.form.get("stock")

        # 1. Uhakiki wa mwanzo (Validation)
        if not all([name, buying_price, selling_price, stock]):
            flash("Tafadhali jaza sehemu zote zilizoachwa wazi.", "warning")
            return redirect(url_for("main.add_product"))

        try:
            # 2. Kubadili data kuwa namba na kuhakikisha ni sahihi
            b_price = float(buying_price)
            s_price = float(selling_price)
            qty = int(stock)

            new_product = Product(
                name=name,
                buying_price=b_price,
                selling_price=s_price,
                stock=qty
            )

            # 3. Kuhifadhi kwenye Database
            db.session.add(new_product)
            db.session.commit()
            
            flash(f"Bidhaa '{name}' imeongezwa kikamilifu! ✅", "success")
            return redirect(url_for("main.dashboard"))

        except ValueError:
            # Hii itatokea kama mtumiaji ataingiza herufi kwenye namba
            flash("Bei na Idadi (Stock) lazima ziwe namba.", "danger")
        except Exception as e:
            # Hii inakamata makosa mengine yoyote (mfano: Database connection)
            db.session.rollback()
            flash("Kuna tatizo limetokea. Jaribu tena baadae.", "danger")
            print(f"Error: {e}") # Kwa ajili ya debugging

    return render_template("add_product.html")

