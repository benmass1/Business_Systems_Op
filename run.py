from app import create_app, db
from app.models import User
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Tengeneza admin wa kwanza kama hayupo
        if not User.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            admin = User(username='admin', password='password123', role='admin')
            db.session.add(admin)
            db.session.commit()
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

