@main.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        # Kwa sasa hatuhifadhi DB, tunapokea tu data
        name = request.form.get("name")
        category = request.form.get("category")
        buy_price = request.form.get("buy_price")
        sell_price = request.form.get("sell_price")
        quantity = request.form.get("quantity")

        flash("Product saved successfully (demo mode)", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_product.html")
