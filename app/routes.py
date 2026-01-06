from flask import Blueprint, render_template, request, redirect, url_for

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # test login (temporary)
        if username == "admin" and password == "admin123":
            return redirect(url_for("main.dashboard"))
        else:
            return render_template("login.html", error="Taarifa si sahihi")

    return render_template("login.html")

@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
