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

    # ⭐ FIX YA FLASK-LOGIN
    @login_manager.user_loader
    def load_user(user_id):
        return None

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from app.sales import sales as sales_blueprint
    app.register_blueprint(sales_blueprint)

    return app

app = create_app()
