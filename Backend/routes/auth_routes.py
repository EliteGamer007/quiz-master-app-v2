from flask import Blueprint, request, jsonify, make_response
# Werkzeug 3.x password hashing uses scrypt algorithm by default (memory-hard function)
# scrypt provides better protection against GPU/ASIC attacks than older pbkdf2
# Hash format: scrypt:32768:8:1$<salt>$<hash> where 32768=CPU cost, 8=block size, 1=parallelization
# generate_password_hash: Creates scrypt hash with auto-generated random salt
# check_password_hash: Extracts salt from stored hash to verify passwords securely
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt,
    set_refresh_cookies, unset_refresh_cookies
)
from models.models import db, User, Admin, QuizMaster, RevokedToken, UserTokenState
from functools import wraps
import datetime
import calendar
import random
import string
from flask_mail import Message
from extensions import mail, limiter

# Import authentication services
from services.register_authority import RegisterAuthority
from services.certificate_provider import CertificateProvider
from services.login_checker import LoginChecker
from services.session_service import SessionService

auth_bp = Blueprint('auth', __name__)

# Initialize authentication services (mail will be set after app context is available)
register_authority = None
certificate_provider = CertificateProvider()
login_checker = None
session_service = SessionService()

def init_auth_services(mail_service):
    """Initialize auth services with Flask-Mail instance after app context is ready."""
    global register_authority, login_checker
    register_authority = RegisterAuthority(mail_service)
    login_checker = LoginChecker(mail_service)

ADMIN_CREDENTIALS = {
    'email': 'admin@quiz.com',
    'password': 'admin123'
}

ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_MINUTES = 120
ABSOLUTE_SESSION_CAP_MINUTES = 120


def _utcnow():
    return datetime.datetime.utcnow()


def _to_datetime_from_unix(unix_ts):
    return datetime.datetime.utcfromtimestamp(unix_ts)


def _create_token_pair(identity, role, session_start=None):
    now = _utcnow()
    session_start = session_start or now
    additional_claims = {
        'role': role,
        'session_start': calendar.timegm(session_start.timetuple())
    }

    access_token = create_access_token(
        identity=identity,
        additional_claims=additional_claims,
        expires_delta=datetime.timedelta(minutes=ACCESS_TOKEN_MINUTES)
    )
    refresh_token = create_refresh_token(
        identity=identity,
        additional_claims=additional_claims,
        expires_delta=datetime.timedelta(minutes=REFRESH_TOKEN_MINUTES)
    )

    return access_token, refresh_token


def _revoke_jwt(jwt_payload):
    jti = jwt_payload.get('jti')
    token_type = jwt_payload.get('type', 'access')
    expires_at_unix = jwt_payload.get('exp')
    identity = jwt_payload.get('identity')

    role = 'admin' if identity == 'admin' else (identity.get('role') if isinstance(identity, dict) else 'unknown')
    user_id = identity.get('id') if isinstance(identity, dict) else None

    if jti and expires_at_unix:
        existing = RevokedToken.query.filter_by(jti=jti).first()
        if existing is None:
            revoked = RevokedToken(
                jti=jti,
                token_type=token_type,
                user_id=user_id,
                role=role,
                expires_at=_to_datetime_from_unix(expires_at_unix)
            )
            db.session.add(revoked)


def _invalidate_all_tokens_for_user(user_id, role):
    state = UserTokenState.query.filter_by(user_id=user_id, role=role).first()
    now = _utcnow()
    if state is None:
        state = UserTokenState(user_id=user_id, role=role, valid_after=now)
        db.session.add(state)
    else:
        state.valid_after = now

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity != 'admin':
            return jsonify({'error': 'Admin access only'}), 403
        return fn(*args, **kwargs)
    return wrapper

def quiz_master_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if not isinstance(identity, dict) or identity.get('role') != 'quiz_master':
            return jsonify({'error': 'Quiz Master access only'}), 403
        return fn(*args, **kwargs)
    return wrapper

def admin_or_quiz_master_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity == 'admin':
            return fn(*args, **kwargs)
        if isinstance(identity, dict) and identity.get('role') == 'quiz_master':
            return fn(*args, **kwargs)
        return jsonify({'error': 'Admin or Quiz Master access required'}), 403
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
@limiter.limit("10/minute")
def request_otp():
    """Step 1: Verify credentials and send OTP"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Admin login - no OTP required
    if email == ADMIN_CREDENTIALS['email'] and password == ADMIN_CREDENTIALS['password']:
        access_token, refresh_token = _create_token_pair(identity='admin', role='admin')
        resp = make_response(jsonify({
            'message': 'Admin login successful',
            'role': 'admin',
            'token': access_token,
            'access_token': access_token,
            'access_expires_in': ACCESS_TOKEN_MINUTES * 60,
            'refresh_expires_in': REFRESH_TOKEN_MINUTES * 60,
            'requires_otp': False
        }), 200)
        set_refresh_cookies(resp, refresh_token)
        return resp

    # Quiz Master login - no OTP required
    quiz_master = QuizMaster.query.filter_by(email=email).first()
    if quiz_master and check_password_hash(quiz_master.password, password):
        identity = {
            'id': quiz_master.id,
            'email': quiz_master.email,
            'role': 'quiz_master',
            'full_name': quiz_master.full_name
        }
        access_token, refresh_token = _create_token_pair(identity=identity, role='quiz_master')
        resp = make_response(jsonify({
            'message': 'Quiz Master login successful',
            'role': 'quiz_master',
            'token': access_token,
            'access_token': access_token,
            'access_expires_in': ACCESS_TOKEN_MINUTES * 60,
            'refresh_expires_in': REFRESH_TOKEN_MINUTES * 60,
            'full_name': quiz_master.full_name,
            'requires_otp': False
        }), 200)
        set_refresh_cookies(resp, refresh_token)
        return resp

    # User login - require OTP
    user = User.query.filter_by(email=email).first()
    # Secure password verification: check_password_hash extracts the salt from the stored
    # scrypt hash (format: scrypt:32768:8:1$salt$hash) and uses it to hash the input password
    # for comparison using constant-time algorithm to prevent timing attacks
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
@limiter.limit("10/minute")
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
    access_token, refresh_token = _create_token_pair(identity=identity, role='user')
    
    resp = make_response(jsonify({
        'message': 'Login successful',
        'role': 'user',
        'token': access_token,
        'access_token': access_token,
        'access_expires_in': ACCESS_TOKEN_MINUTES * 60,
        'refresh_expires_in': REFRESH_TOKEN_MINUTES * 60,
        'full_name': user.full_name
    }), 200)
    set_refresh_cookies(resp, refresh_token)
    return resp

@auth_bp.route('/login', methods=['POST'])
def login():
    """Deprecated: Use /request-otp instead"""
    return request_otp()

# ============================================================================
# SERVICE-BASED AUTHENTICATION ROUTES
# These routes use the modular service architecture:
# - Registration: RegisterAuthority -> CertificateProvider
# - Login: LoginChecker -> SessionService
# ============================================================================

@auth_bp.route('/v2/register', methods=['POST'])
@limiter.limit("8/minute")
def register_v2():
    """
    Service-based registration (Step 1): Submit registration to Register Authority.
    
    Flow: User -> RegisterAuthority (validate & authorize) -> OTP sent
    """
    if not register_authority:
        init_auth_services(mail)
    
    data = request.get_json()
    success, result = register_authority.authorize_registration(data)
    
    if success:
        return jsonify(result), 200
    else:
        status_code = 409 if 'already exists' in result.get('error', '') else 400
        return jsonify(result), status_code

@auth_bp.route('/v2/verify-registration', methods=['POST'])
@limiter.limit("10/minute")
def verify_registration_v2():
    """
    Service-based registration (Step 2): Verify OTP and create account via Certificate Provider.
    
    Flow: OTP verified -> CertificateProvider (create account) -> Account created
    """
    if not register_authority:
        init_auth_services(mail)
    
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    # Step 1: Verify OTP with Register Authority
    is_valid, result = register_authority.verify_otp(email, otp)
    
    if not is_valid:
        return jsonify({'error': result}), 400
    
    # Step 2: Create account with Certificate Provider
    success, cert_result = certificate_provider.create_user_certificate(result)
    
    if success:
        # Clean up pending registration
        register_authority.clear_pending_registration(email)
        return jsonify(cert_result), 201
    else:
        return jsonify(cert_result), 500

@auth_bp.route('/v2/login', methods=['POST'])
@limiter.limit("10/minute")
def login_v2():
    """
    Service-based login (Step 1): Verify credentials with Login Checker.
    
    Flow: User -> LoginChecker (verify credentials) -> OTP sent (for users) or Session created
    """
    if not login_checker:
        init_auth_services(mail)
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Verify credentials with Login Checker
    success, result = login_checker.verify_credentials(email, password)
    
    if not success:
        return jsonify(result), 401
    
    role = result['role']
    entity = result['entity']
    
    # Admin and Quiz Master don't need OTP - create session directly
    if not result['requires_otp']:
        session_data = session_service.create_session(role, entity)
        session_data['requires_otp'] = False
        return jsonify(session_data), 200
    
    # User requires OTP - initiate OTP verification
    user = login_checker.get_user_by_email(email)
    otp_success, otp_message = login_checker.initiate_otp_verification(user)
    
    if otp_success:
        return jsonify({
            'message': otp_message,
            'requires_otp': True,
            'email': email
        }), 200
    else:
        return jsonify({'error': otp_message}), 500

@auth_bp.route('/v2/verify-login-otp', methods=['POST'])
@limiter.limit("10/minute")
def verify_login_otp_v2():
    """
    Service-based login (Step 2): Verify OTP and create session via Session Service.
    
    Flow: OTP verified -> SessionService (create session) -> JWT Token returned
    """
    if not login_checker:
        init_auth_services(mail)
    
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    # Verify OTP with Login Checker
    is_valid, result = login_checker.verify_otp(email, otp)
    
    if not is_valid:
        return jsonify({'error': result}), 401
    
    # Create session with Session Service
    user = result
    user_data = {
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'qualification': user.qualification
    }
    
    session_data = session_service.create_user_session(user_data)
    return jsonify(session_data), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@limiter.limit("20/minute")
def refresh_access_token():
    jwt_payload = get_jwt()
    identity = get_jwt_identity()

    session_start_unix = jwt_payload.get('session_start')
    if session_start_unix is None:
        return jsonify({'error': 'Invalid refresh token'}), 401

    session_start = _to_datetime_from_unix(session_start_unix)
    if (_utcnow() - session_start) > datetime.timedelta(minutes=ABSOLUTE_SESSION_CAP_MINUTES):
        _revoke_jwt(jwt_payload)
        db.session.commit()
        return jsonify({'error': 'Session expired. Please login again.'}), 401

    role = 'admin' if identity == 'admin' else (identity.get('role') if isinstance(identity, dict) else None)
    if role not in ('admin', 'quiz_master', 'user'):
        return jsonify({'error': 'Invalid token role'}), 401

    _revoke_jwt(jwt_payload)
    access_token, refresh_token = _create_token_pair(identity=identity, role=role, session_start=session_start)
    db.session.commit()

    resp = make_response(jsonify({
        'access_token': access_token,
        'token': access_token,
        'access_expires_in': ACCESS_TOKEN_MINUTES * 60,
        'refresh_expires_in': REFRESH_TOKEN_MINUTES * 60
    }), 200)
    set_refresh_cookies(resp, refresh_token)
    return resp


@auth_bp.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)
@limiter.limit("30/minute")
def logout():
    jwt_payload = get_jwt()
    _revoke_jwt(jwt_payload)

    # Try to revoke refresh token from cookie
    refresh_cookie = request.cookies.get('refresh_token_cookie')
    if refresh_cookie:
        try:
            from flask_jwt_extended import decode_token
            refresh_payload = decode_token(refresh_cookie)
            if refresh_payload.get('type') == 'refresh':
                _revoke_jwt(refresh_payload)
        except Exception:
            pass

    # Also check JSON body for backward compat
    data = request.get_json(silent=True) or {}
    refresh_token_body = data.get('refresh_token')
    if refresh_token_body:
        try:
            from flask_jwt_extended import decode_token
            refresh_payload = decode_token(refresh_token_body)
            if refresh_payload.get('type') == 'refresh':
                _revoke_jwt(refresh_payload)
        except Exception:
            pass

    db.session.commit()
    resp = make_response(jsonify({'message': 'Logged out successfully'}), 200)
    unset_refresh_cookies(resp)
    return resp

# ============================================================================
# FORGOT PASSWORD ROUTES
# ============================================================================

@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("8/minute")
def forgot_password():
    """
    Step 1: Request password reset OTP.
    
    Flow: User submits email -> OTP sent to email
    """
    if not login_checker:
        init_auth_services(mail)
    
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    success, message = login_checker.initiate_password_reset(email)
    
    if success:
        return jsonify({'message': message, 'email': email}), 200
    else:
        return jsonify({'error': message}), 500

@auth_bp.route('/verify-reset-otp', methods=['POST'])
@limiter.limit("10/minute")
def verify_reset_otp():
    """
    Step 2: Verify OTP for password reset.
    
    Flow: User submits OTP -> OTP verified
    """
    if not login_checker:
        init_auth_services(mail)
    
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400
    
    is_valid, result = login_checker.verify_reset_otp(email, otp)
    
    if is_valid:
        return jsonify({'message': 'OTP verified', 'verified': True}), 200
    else:
        return jsonify({'error': result, 'verified': False}), 400

@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("10/minute")
def reset_password():
    """
    Step 3: Reset password after OTP verification.
    
    Flow: User submits new password -> Password updated
    """
    if not login_checker:
        init_auth_services(mail)
    
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not all([email, otp, new_password, confirm_password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    success, message = login_checker.reset_password(email, otp, new_password)
    
    if success:
        user = User.query.filter_by(email=email).first()
        if user:
            _invalidate_all_tokens_for_user(user.id, 'user')
            db.session.commit()
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400

# ============================================================================
# LEGACY ROUTES (kept for backward compatibility)
# ============================================================================

# Temporary storage for pending registrations (in production, use Redis or database table)
pending_registrations = {}

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("8/minute")
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
@limiter.limit("10/minute")
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
        # Password hashing with scrypt: Werkzeug 3.x uses scrypt algorithm by default
        # scrypt is a memory-hard function providing better security against GPU/ASIC attacks
        # A random salt is generated and embedded in the hash (format: scrypt:32768:8:1$<salt>$<hash>)
        # Parameters: N=32768 (CPU cost), r=8 (block size), p=1 (parallelization)
        hashed_password = generate_password_hash(registration_data['password'])
        new_user = User(
            full_name=registration_data['name'],
            email=registration_data['email'],
            password=hashed_password,  # Stored as: "scrypt:32768:8:1$randomsalt$hashedvalue"
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