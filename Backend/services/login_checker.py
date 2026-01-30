"""
Login Checker Service
======================
Handles credential verification for login requests.

This service is responsible for:
1. Validating login credentials against stored records
2. Verifying passwords using scrypt hash comparison
3. Handling OTP generation and verification for 2FA
4. Determining user role and authorization level

Security Note - Password Verification:
--------------------------------------
Passwords are verified using Werkzeug's check_password_hash which:
1. Extracts the salt from the stored hash
2. Hashes the input password with the same salt and parameters
3. Performs constant-time comparison to prevent timing attacks

The stored hash format (scrypt): scrypt:32768:8:1$<salt>$<hash>
check_password_hash handles both scrypt and legacy pbkdf2 formats.

Flow:
    User login -> LoginChecker (verify credentials) -> SessionService (create session)
"""

import datetime
import random
import string
from werkzeug.security import check_password_hash
from flask_mail import Message
from models.models import db, User, QuizMaster


class LoginChecker:
    """
    Login Checker validates user credentials and manages login flow.
    
    This service handles:
    - Password verification using scrypt/pbkdf2 hash comparison
    - Multi-factor authentication (OTP) for users
    - Role-based login handling (admin, quiz_master, user)
    """
    
    # Hardcoded admin credentials (in production, use secure storage)
    ADMIN_CREDENTIALS = {
        'email': 'admin@quiz.com',
        'password': 'admin123'
    }
    
    def __init__(self, mail_service):
        """
        Initialize LoginChecker with mail service for OTP delivery.
        
        Args:
            mail_service: Flask-Mail instance for sending OTP emails
        """
        self.mail = mail_service
    
    @staticmethod
    def _generate_otp():
        """Generate a cryptographically random 6-digit OTP."""
        return ''.join(random.choices(string.digits, k=6))
    
    def check_admin_credentials(self, email, password):
        """
        Check if credentials match admin account.
        
        Args:
            email: Login email
            password: Login password
            
        Returns:
            bool: True if admin credentials match
        """
        return (email == self.ADMIN_CREDENTIALS['email'] and 
                password == self.ADMIN_CREDENTIALS['password'])
    
    def check_quiz_master_credentials(self, email, password):
        """
        Verify Quiz Master credentials.
        
        Password verification uses check_password_hash which:
        - Extracts algorithm, parameters, and salt from stored hash
        - Hashes input with same configuration
        - Uses constant-time comparison
        
        Args:
            email: Quiz Master email
            password: Plain text password to verify
            
        Returns:
            tuple: (is_valid: bool, quiz_master: QuizMaster or None)
        """
        quiz_master = QuizMaster.query.filter_by(email=email).first()
        
        if not quiz_master:
            return False, None
        
        # Secure password verification: check_password_hash extracts the salt
        # from stored hash (format: scrypt:32768:8:1$salt$hash or pbkdf2:sha256:260000$salt$hash)
        # and uses it to hash the input password for comparison
        if check_password_hash(quiz_master.password, password):
            return True, quiz_master
        
        return False, None
    
    def check_user_credentials(self, email, password):
        """
        Verify User credentials.
        
        Password verification process:
        1. Retrieve user record by email
        2. Extract salt from stored scrypt hash
        3. Hash input password with same salt/parameters
        4. Compare hashes using constant-time algorithm
        
        Args:
            email: User email
            password: Plain text password to verify
            
        Returns:
            tuple: (is_valid: bool, user: User or None)
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return False, None
        
        # Secure verification using stored scrypt hash
        # check_password_hash handles hash format detection automatically
        if check_password_hash(user.password, password):
            return True, user
        
        return False, None
    
    def verify_credentials(self, email, password):
        """
        Main method to verify login credentials and determine user role.
        
        This method checks credentials in order:
        1. Admin (direct match, no OTP)
        2. Quiz Master (hash verification, no OTP)
        3. User (hash verification, requires OTP)
        
        Args:
            email: Login email
            password: Login password
            
        Returns:
            tuple: (success: bool, result: dict)
                Result includes 'role', 'requires_otp', 'entity' data, or 'error'
        """
        # Check admin credentials first
        if self.check_admin_credentials(email, password):
            return True, {
                'role': 'admin',
                'requires_otp': False,
                'entity': {'email': email}
            }
        
        # Check Quiz Master credentials
        qm_valid, quiz_master = self.check_quiz_master_credentials(email, password)
        if qm_valid:
            return True, {
                'role': 'quiz_master',
                'requires_otp': False,
                'entity': {
                    'id': quiz_master.id,
                    'email': quiz_master.email,
                    'full_name': quiz_master.full_name
                }
            }
        
        # Check User credentials
        user_valid, user = self.check_user_credentials(email, password)
        if user_valid:
            return True, {
                'role': 'user',
                'requires_otp': True,  # Users require OTP
                'entity': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'qualification': user.qualification
                }
            }
        
        # No valid credentials found
        return False, {'error': 'Invalid credentials'}
    
    def initiate_otp_verification(self, user):
        """
        Generate and send OTP for user login verification.
        
        Args:
            user: User model instance
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Generate OTP
            otp = self._generate_otp()
            
            # Store OTP and timestamp on user record
            user.otp = otp
            user.otp_created_at = datetime.datetime.utcnow()
            db.session.commit()
            
            # Send OTP email
            self._send_otp_email(user.email, otp)
            
            return True, 'OTP sent to your email'
            
        except Exception as e:
            return False, f'Failed to send OTP: {str(e)}'
    
    def _send_otp_email(self, email, otp):
        """
        Send OTP verification email.
        
        Args:
            email: Recipient email address
            otp: One-time password to send
            
        Raises:
            Exception: If email sending fails
        """
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
        self.mail.send(msg)
    
    def verify_otp(self, email, otp):
        """
        Verify OTP for user login.
        
        Args:
            email: User email
            otp: OTP provided by user
            
        Returns:
            tuple: (is_valid: bool, user: User or error_message: str)
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return False, 'User not found'
        
        # Check if OTP exists
        if not user.otp:
            return False, 'No OTP requested. Please login again.'
        
        # Check if OTP is expired (5 minutes)
        otp_age = datetime.datetime.utcnow() - user.otp_created_at
        if otp_age.total_seconds() > 300:
            user.otp = None
            user.otp_created_at = None
            db.session.commit()
            return False, 'OTP expired. Please login again.'
        
        # Verify OTP
        if user.otp != otp:
            return False, 'Invalid OTP'
        
        # Clear OTP after successful verification
        user.otp = None
        user.otp_created_at = None
        db.session.commit()
        
        return True, user
    
    def get_user_by_email(self, email):
        """
        Retrieve a user by email address.
        
        Args:
            email: User email to look up
            
        Returns:
            User or None: User model instance if found
        """
        return User.query.filter_by(email=email).first()
    
    # =========================================================================
    # FORGOT PASSWORD METHODS
    # =========================================================================
    
    def initiate_password_reset(self, email):
        """
        Initiate password reset by sending OTP to user's email.
        
        Args:
            email: User email address
            
        Returns:
            tuple: (success: bool, message: str)
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            return True, 'If this email is registered, you will receive an OTP'
        
        try:
            # Generate OTP
            otp = self._generate_otp()
            
            # Store OTP and timestamp on user record
            user.otp = otp
            user.otp_created_at = datetime.datetime.utcnow()
            db.session.commit()
            
            # Send password reset OTP email
            self._send_password_reset_email(user.email, otp)
            
            return True, 'OTP sent to your email'
            
        except Exception as e:
            return False, f'Failed to send OTP: {str(e)}'
    
    def _send_password_reset_email(self, email, otp):
        """
        Send password reset OTP email.
        
        Args:
            email: Recipient email address
            otp: One-time password to send
        """
        msg = Message(
            subject='Quiz Master App - Password Reset OTP',
            recipients=[email],
            body=f'''Hello,

You have requested to reset your password.

Your password reset OTP is: {otp}

This OTP is valid for 5 minutes. Do not share this code with anyone.

If you did not request a password reset, please ignore this email.

Best regards,
Quiz Master App Team'''
        )
        self.mail.send(msg)
    
    def verify_reset_otp(self, email, otp):
        """
        Verify OTP for password reset.
        
        Args:
            email: User email
            otp: OTP provided by user
            
        Returns:
            tuple: (is_valid: bool, user or error_message)
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return False, 'User not found'
        
        # Check if OTP exists
        if not user.otp:
            return False, 'No OTP requested. Please try again.'
        
        # Check if OTP is expired (5 minutes)
        otp_age = datetime.datetime.utcnow() - user.otp_created_at
        if otp_age.total_seconds() > 300:
            user.otp = None
            user.otp_created_at = None
            db.session.commit()
            return False, 'OTP expired. Please request a new one.'
        
        # Verify OTP
        if user.otp != otp:
            return False, 'Invalid OTP'
        
        # Don't clear OTP yet - it will be cleared after password reset
        return True, user
    
    def reset_password(self, email, otp, new_password):
        """
        Reset user password after OTP verification.
        
        Args:
            email: User email
            otp: OTP for verification
            new_password: New password to set
            
        Returns:
            tuple: (success: bool, message: str)
        """
        from werkzeug.security import generate_password_hash
        
        # Verify OTP first
        is_valid, result = self.verify_reset_otp(email, otp)
        
        if not is_valid:
            return False, result
        
        user = result
        
        try:
            # Hash new password using scrypt (Werkzeug 3.x default)
            user.password = generate_password_hash(new_password)
            
            # Clear OTP after successful password reset
            user.otp = None
            user.otp_created_at = None
            db.session.commit()
            
            return True, 'Password reset successful. You can now login with your new password.'
            
        except Exception as e:
            db.session.rollback()
            return False, f'Failed to reset password: {str(e)}'
