from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from models.models import db, User
from functools import wraps
import datetime

auth_bp = Blueprint('auth', __name__)

ADMIN_CREDENTIALS = {
    'email': 'admin@quiz.com',
    'password': 'admin123'
}

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_jwt_identity()
        if user.get('role') != 'admin':
            return jsonify({'error': 'Admin access only'}), 403
        return fn(*args, **kwargs)
    return wrapper

def user_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = get_jwt_identity()
        if user.get('role') != 'user':
            return jsonify({'error': 'User access only'}), 403
        return fn(*args, **kwargs)
    return wrapper

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if email == ADMIN_CREDENTIALS['email'] and password == ADMIN_CREDENTIALS['password']:
        access_token = create_access_token(
            identity={'email': email, 'role': 'admin'},
            expires_delta=datetime.timedelta(hours=2)
        )
        return jsonify({
            'message': 'Admin login successful',
            'role': 'admin',
            'token': access_token
        }), 200

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        identity = {
            'id': user.id,
            'email': user.email,
            'role': 'user',
            'qualification': user.qualification
        }
        token = create_access_token(identity=identity, expires_delta=datetime.timedelta(hours=2))
        return jsonify({
            'message': 'Login successful',
            'role': 'user',
            'token': token
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409

    hashed_password = generate_password_hash(data['password'])

    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        qualification=data.get('qualification'),
        age=data.get('age')
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201
@auth_bp.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    return jsonify({'message': 'Welcome Admin!'}), 200

@auth_bp.route('/user/profile', methods=['GET'])
@user_required
def user_profile():
    user = get_jwt_identity()
    return jsonify({
        'message': f"Welcome {user.get('email')}",
        'qualification': user.get('qualification')
    }), 200
