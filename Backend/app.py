from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.pool import NullPool
from extensions import db, mail, cache, limiter
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key-ig')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-jwt')
    app.config['JWT_IDENTITY_CLAIM'] = 'identity'
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'poolclass': NullPool}
    
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Email configuration from environment variables
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/1'
    
    app.config['RATELIMIT_STORAGE_URL'] = 'redis://localhost:6379/2'
    
    CORS(app, supports_credentials=True, origins="http://localhost:8080")

    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    JWTManager(app)

    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.user_routes import user_bp
    from routes.quiz_master_routes import quiz_master_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(quiz_master_bp, url_prefix='/api/quiz-master')
    
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()

    app.run(debug=True, port=8000)
