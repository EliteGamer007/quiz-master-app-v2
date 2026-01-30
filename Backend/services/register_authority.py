"""
Register Authority Service
===========================
Handles the first step of user registration - validation and authorization.

This service is responsible for:
1. Validating registration data (email format, required fields)
2. Checking if user already exists
3. Generating and sending OTP for email verification
4. Temporarily storing pending registration data

Flow:
    User -> RegisterAuthority (validate & authorize) -> CertificateProvider (create account)
"""

import datetime
import random
import string
from flask_mail import Message
from models.models import User


class RegisterAuthority:
    """
    Registration Authority handles validation and authorization of new user registrations.
    
    This follows the separation of concerns principle:
    - RegisterAuthority: Validates and authorizes the registration request
    - CertificateProvider: Actually creates the user account after verification
    """
    
    # Temporary storage for pending registrations
    # In production, use Redis or a dedicated database table
    _pending_registrations = {}
    
    def __init__(self, mail_service):
        """
        Initialize RegisterAuthority with mail service for OTP delivery.
        
        Args:
            mail_service: Flask-Mail instance for sending verification emails
        """
        self.mail = mail_service
        
    @staticmethod
    def _generate_otp():
        """Generate a cryptographically random 6-digit OTP."""
        return ''.join(random.choices(string.digits, k=6))
    
    def validate_registration_data(self, data):
        """
        Validate the registration request data.
        
        Args:
            data: Dictionary containing registration fields
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        required_fields = ['name', 'email', 'password']
        
        for field in required_fields:
            if not data.get(field):
                return False, f"Missing required field: {field}"
        
        email = data.get('email', '')
        if '@' not in email or '.' not in email:
            return False, "Invalid email format"
        
        password = data.get('password', '')
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
            
        return True, None
    
    def check_user_exists(self, email):
        """
        Check if a user with the given email already exists.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if user exists, False otherwise
        """
        return User.query.filter_by(email=email).first() is not None
    
    def authorize_registration(self, data):
        """
        Main method to authorize a registration request.
        
        This method:
        1. Validates the registration data
        2. Checks for existing users
        3. Generates OTP
        4. Stores pending registration
        5. Sends verification email
        
        Args:
            data: Registration request data containing name, email, password, etc.
            
        Returns:
            tuple: (success: bool, result: dict)
                - On success: (True, {'message': str, 'email': str, 'requires_otp': True})
                - On failure: (False, {'error': str})
        """
        # Step 1: Validate registration data
        is_valid, error = self.validate_registration_data(data)
        if not is_valid:
            return False, {'error': error}
        
        email = data.get('email')
        
        # Step 2: Check if user already exists
        if self.check_user_exists(email):
            return False, {'error': 'User already exists'}
        
        # Step 3: Generate OTP for verification
        otp = self._generate_otp()
        
        # Step 4: Store pending registration data
        self._pending_registrations[email] = {
            'name': data.get('name'),
            'email': email,
            'password': data.get('password'),
            'qualification': data.get('qualification'),
            'age': data.get('age'),
            'otp': otp,
            'created_at': datetime.datetime.utcnow(),
            'status': 'pending_verification'
        }
        
        # Step 5: Send verification email
        try:
            self._send_verification_email(email, otp)
            return True, {
                'message': 'OTP sent to your email',
                'requires_otp': True,
                'email': email
            }
        except Exception as e:
            # Clean up pending registration on email failure
            self._pending_registrations.pop(email, None)
            return False, {'error': f'Failed to send verification email: {str(e)}'}
    
    def _send_verification_email(self, email, otp):
        """
        Send OTP verification email to the user.
        
        Args:
            email: Recipient email address
            otp: One-time password to send
            
        Raises:
            Exception: If email sending fails
        """
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
        self.mail.send(msg)
    
    def verify_otp(self, email, otp):
        """
        Verify the OTP for a pending registration.
        
        Args:
            email: Email address of pending registration
            otp: OTP provided by user
            
        Returns:
            tuple: (is_valid: bool, registration_data: dict or error_message: str)
        """
        if email not in self._pending_registrations:
            return False, 'Registration not found. Please register again.'
        
        registration_data = self._pending_registrations[email]
        
        # Check if OTP is expired (5 minutes)
        otp_age = datetime.datetime.utcnow() - registration_data['created_at']
        if otp_age.total_seconds() > 300:
            self._pending_registrations.pop(email, None)
            return False, 'OTP expired. Please register again.'
        
        # Verify OTP
        if registration_data['otp'] != otp:
            return False, 'Invalid OTP'
        
        # Mark as verified and return data for certificate provider
        registration_data['status'] = 'verified'
        return True, registration_data
    
    def clear_pending_registration(self, email):
        """
        Remove a pending registration from temporary storage.
        Called after successful account creation or expiration.
        
        Args:
            email: Email address to clear
        """
        self._pending_registrations.pop(email, None)
    
    def get_pending_registration(self, email):
        """
        Get pending registration data for an email.
        
        Args:
            email: Email address to look up
            
        Returns:
            dict or None: Registration data if exists
        """
        return self._pending_registrations.get(email)
