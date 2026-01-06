from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize extensions nje ya create_app
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login" # Hii iendane na jina la route yako ya login
login_manager.login_message_category = "info" # Inapendezesha rangi ya ujumbe wa login

def create_app():
    app = Flask(__name__)

    # Mipangilio (Configuration)
    # Ni vizuri kutumia Environment Variables kwa SECRET_KEY kwa usalama
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "business_secret_2026")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///business.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions na app context
    db.init_app(app)
    login_manager.init_app(app)

    # 1. User Loader (Hii ni muhimu kwa Flask-Login kufanya kazi)
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 2. Sajili Blueprints
    from app.routes import main
    app.register_blueprint(main)

    # 3. Tengeneza Database endapo haipo
    with app.app_context():
        # Hii ni salama, haifuti data kama database tayari ipo
        db.create_all()

    return app

