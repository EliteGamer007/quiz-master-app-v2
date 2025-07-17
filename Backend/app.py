from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models.models import db
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'super-secret-key-ig'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-key-jwt'
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  

    CORS(app, supports_credentials=True, origins="http://localhost:5173")
    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8000)
