from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app.models import User
from app import db

auth = Blueprint('auth', __name__)

# ======================
# LOGIN
# ======================
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # ⚠ kwa sasa bado plain password (tutaboreshwa baadaye)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('sales.dashboard'))

        flash('Username au Password sio sahihi!', 'danger')

    return render_template('login.html')


# ======================
# LOGOUT
# ======================
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
