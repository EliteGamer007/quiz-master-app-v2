from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models.models import db
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key-ig'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-key-jwt'

    CORS(app, supports_credentials=True, origins="http://localhost:8080")

    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8000)
