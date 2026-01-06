from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "business_secret_2026"

    from app.routes import main
    app.register_blueprint(main)

    return app
