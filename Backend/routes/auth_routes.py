from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from models.models import db, User
from functools import wraps
import datetime
import random
import string
from flask_mail import Message
from extensions import mail

auth_bp = Blueprint('auth', __name__)

ADMIN_CREDENTIALS = {
    'email': 'admin@quiz.com',
    'password': 'admin123'
}

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity != 'admin':
            return jsonify({'error': 'Admin access only'}), 403
        return fn(*args, **kwargs)
    return wrapper

def user_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if isinstance(identity, dict) and identity.get('role') == 'user':
            return fn(*args, **kwargs)
        return jsonify({'error': 'User access only'}), 403
    return wrapper

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via email using Flask-Mail"""
    try:
        msg = Message(
            subject='Quiz Master App - Your Login OTP',
            recipients=[email],
            body=f'''Hello,

Your OTP for login is: {otp}

This OTP is valid for 5 minutes. Do not share this code with anyone.

If you did not request this, please ignore this email.

Best regards,
Quiz Master App Team'''
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@auth_bp.route('/request-otp', methods=['POST'])
def request_otp():
    """Step 1: Verify credentials and send OTP"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Admin login - no OTP required
    if email == ADMIN_CREDENTIALS['email'] and password == ADMIN_CREDENTIALS['password']:
        token = create_access_token(identity='admin', expires_delta=datetime.timedelta(hours=2))
        return jsonify({
            'message': 'Admin login successful',
            'role': 'admin',
            'token': token,
            'requires_otp': False
        }), 200

    # User login - require OTP
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate and store OTP
    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.datetime.utcnow()
    db.session.commit()

    # Send OTP email
    if send_otp_email(email, otp):
        return jsonify({
            'message': 'OTP sent to your email',
            'requires_otp': True,
            'email': email
        }), 200
    else:
        return jsonify({'error': 'Failed to send OTP. Please try again.'}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Step 2: Verify OTP and complete login"""
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if OTP exists
    if not user.otp:
        return jsonify({'error': 'No OTP requested. Please login again.'}), 400

    # Check if OTP is expired (5 minutes)
    otp_age = datetime.datetime.utcnow() - user.otp_created_at
    if otp_age.total_seconds() > 300:  # 5 minutes
        user.otp = None
        user.otp_created_at = None
        db.session.commit()
        return jsonify({'error': 'OTP expired. Please login again.'}), 400

    # Verify OTP
    if user.otp != otp:
        return jsonify({'error': 'Invalid OTP'}), 401

    # Clear OTP after successful verification
    user.otp = None
    user.otp_created_at = None
    db.session.commit()

    # Create JWT token
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
        'token': token,
        'full_name': user.full_name
    }), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    """Deprecated: Use /request-otp instead"""
    return request_otp()

# Temporary storage for pending registrations (in production, use Redis or database table)
pending_registrations = {}

@auth_bp.route('/register', methods=['POST'])
def register():
    """Step 1: Validate registration data and send OTP"""
    data = request.get_json()
    email = data.get('email')

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 409

    # Generate OTP
    otp = generate_otp()
    
    # Store registration data temporarily with OTP
    pending_registrations[email] = {
        'name': data.get('name'),
        'email': email,
        'password': data.get('password'),
        'qualification': data.get('qualification'),
        'age': data.get('age'),
        'otp': otp,
        'created_at': datetime.datetime.utcnow()
    }
    
    # Send OTP email
    try:
        msg = Message(
            subject='Quiz Master - Verify Your Registration',
            recipients=[email],
            body=f'''Welcome to Quiz Master!

Your verification OTP is: {otp}

This OTP is valid for 5 minutes. Enter it to complete your registration.

If you did not register for this account, please ignore this email.

Best regards,
Quiz Master Team'''
        )
        mail.send(msg)
        return jsonify({
            'message': 'OTP sent to your email',
            'requires_otp': True,
            'email': email
        }), 200
    except Exception as e:
        print(f"Error sending registration email: {e}")
        # Clean up pending registration
        pending_registrations.pop(email, None)
        return jsonify({'error': 'Failed to send verification email. Please try again.'}), 500

@auth_bp.route('/verify-registration-otp', methods=['POST'])
def verify_registration_otp():
    """Step 2: Verify OTP and complete registration"""
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    # Check if registration exists
    if email not in pending_registrations:
        return jsonify({'error': 'Registration not found. Please register again.'}), 404

    registration_data = pending_registrations[email]

    # Check if OTP is expired (5 minutes)
    otp_age = datetime.datetime.utcnow() - registration_data['created_at']
    if otp_age.total_seconds() > 300:
        pending_registrations.pop(email, None)
        return jsonify({'error': 'OTP expired. Please register again.'}), 400

    # Verify OTP
    if registration_data['otp'] != otp:
        return jsonify({'error': 'Invalid OTP'}), 401

    # Create user account
    try:
        hashed_password = generate_password_hash(registration_data['password'])
        new_user = User(
            full_name=registration_data['name'],
            email=registration_data['email'],
            password=hashed_password,
            qualification=registration_data.get('qualification'),
            age=registration_data.get('age')
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Clean up pending registration
        pending_registrations.pop(email, None)
        
        return jsonify({'message': 'Registration successful! You can now login.'}), 201
    except Exception as e:
        print(f"Error creating user: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

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