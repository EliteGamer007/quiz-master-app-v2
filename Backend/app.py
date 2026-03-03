from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.pool import NullPool
from extensions import db, mail, cache, limiter
import os
import socket
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()


def is_true(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def can_connect(host, port, timeout=0.2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key-ig')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        raise RuntimeError('JWT_SECRET_KEY is required. Set it in environment/.env before starting the app.')
    app.config['JWT_SECRET_KEY'] = jwt_secret
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
    
    redis_available = can_connect('localhost', 6379)

    if redis_available:
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = os.getenv('CACHE_REDIS_URL', 'redis://localhost:6379/1')
        app.config['RATELIMIT_STORAGE_URL'] = 'redis://localhost:6379/2'
    else:
        app.config['CACHE_TYPE'] = 'SimpleCache'
        app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
    
    cors_origins_raw = os.getenv('CORS_ORIGINS', 'http://localhost:3000,https://localhost:3000')
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(',') if origin.strip()]
    CORS(app, supports_credentials=True, origins=cors_origins)

    db.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900   # 15 minutes
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 7200  # 120 minutes

    # --- HttpOnly cookie storage for refresh tokens ---
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = is_true(os.getenv('FLASK_SSL_ENABLED', 'false'))
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/api/auth/'

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        from models.models import RevokedToken, UserTokenState

        jti = jwt_payload.get('jti')
        if not jti:
            return True

        if RevokedToken.query.filter_by(jti=jti).first() is not None:
            return True

        identity = jwt_payload.get('identity')
        if isinstance(identity, dict):
            role = identity.get('role')
            user_id = identity.get('id')
            if role in ('user', 'quiz_master') and user_id is not None:
                state = UserTokenState.query.filter_by(user_id=user_id, role=role).first()
                if state:
                    iat = jwt_payload.get('iat')
                    if iat is not None:
                        issued_at = datetime.fromtimestamp(iat, tz=timezone.utc).replace(tzinfo=None)
                        if issued_at < state.valid_after:
                            return True

        return False

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
    debug_mode = is_true(os.getenv('FLASK_DEBUG', 'true'))
    port = int(os.getenv('BACKEND_PORT', '5000'))

    ssl_enabled = is_true(os.getenv('FLASK_SSL_ENABLED', 'false'))
    cert_file = os.getenv('FLASK_SSL_CERT_FILE', 'cert.pem')
    key_file = os.getenv('FLASK_SSL_KEY_FILE', 'key.pem')

    if ssl_enabled:
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            raise RuntimeError(
                f"SSL is enabled but certificate files were not found. "
                f"Expected cert={cert_file}, key={key_file}."
            )
        app.run(debug=debug_mode, port=port, ssl_context=(cert_file, key_file))
    else:
        app.run(debug=debug_mode, port=port)
