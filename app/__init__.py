from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # =====================
    # USER LOADER
    # =====================
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # =====================
    # CREATE TABLES (MUHIMU SANA)
    # =====================
    with app.app_context():
        db.create_all()

    # =====================
    # REGISTER BLUEPRINTS
    # =====================
    from app.auth.routes import auth
    app.register_blueprint(auth)

    from app.sales import sales
    app.register_blueprint(sales)

    return app


# GUNICORN ENTRY POINT
app = create_app()
