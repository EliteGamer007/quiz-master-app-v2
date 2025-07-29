from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from models.models import db
from sqlalchemy.pool import NullPool
import os

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key-ig'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-key-jwt'
    app.config['JWT_IDENTITY_CLAIM'] = 'identity'
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'poolclass': NullPool}
    
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'sanjeevevps@gmail.com'
    app.config['MAIL_PASSWORD'] = 'lpud dnfz ljnt chct'
    app.config['MAIL_DEFAULT_SENDER'] = 'sanjeevevps@gmail.com'

    CORS(app, supports_credentials=True, origins="http://localhost:8080")

    db.init_app(app)
    JWTManager(app)
    mail.init_app(app)

    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.user_routes import user_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8000)