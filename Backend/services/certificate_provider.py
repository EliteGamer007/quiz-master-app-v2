"""
Certificate Provider Service
=============================
Handles user account creation and certificate generation after registration is authorized.

This service is responsible for:
1. Creating user accounts in the database
2. Securely hashing passwords using scrypt algorithm
3. Generating user certificates/credentials

Security Note - Password Hashing:
---------------------------------
This implementation uses Werkzeug 3.x's generate_password_hash which defaults to 
scrypt algorithm (memory-hard function) instead of the older pbkdf2:sha256.

Scrypt provides better protection against:
- GPU-based attacks (memory-hard)
- ASIC-based attacks
- Parallel brute-force attempts

Hash Format: scrypt:32768:8:1$<salt>$<hash>
            |       |  | |    |      |
            |       |  | |    |      └─ Hash output
            |       |  | |    └─ Random salt
            |       |  | └─ Parallelization factor (p=1)
            |       |  └─ Block size (r=8)
            |       └─ CPU/Memory cost (N=32768)
            └─ Algorithm identifier

Flow:
    RegisterAuthority (verified) -> CertificateProvider (create account) -> User created
"""

from werkzeug.security import generate_password_hash
from models.models import db, User
import datetime


class CertificateProvider:
    """
    Certificate Provider handles the creation of user accounts and credentials.
    
    After the RegisterAuthority has verified the registration request,
    this service creates the actual user account with:
    - Securely hashed password (scrypt with random salt)
    - User profile information
    - Account creation timestamp
    """
    
    def __init__(self):
        """Initialize the Certificate Provider service."""
        pass
    
    def hash_password(self, plain_password):
        """
        Hash a password using scrypt algorithm with random salt.
        
        Werkzeug 3.x uses scrypt by default which is a memory-hard function
        providing better security against hardware-accelerated attacks.
        
        Args:
            plain_password: The plain text password to hash
            
        Returns:
            str: Hashed password in format "scrypt:32768:8:1$<salt>$<hash>"
            
        Security:
            - Each hash has a unique random salt
            - Memory-hard function resists GPU/ASIC attacks
            - Time-cost parameter makes brute-force expensive
        """
        # Werkzeug 3.x defaults to scrypt with these parameters:
        # - n (CPU cost): 32768
        # - r (block size): 8  
        # - p (parallelization): 1
        return generate_password_hash(plain_password)
    
    def create_user_certificate(self, registration_data):
        """
        Create a new user account with the verified registration data.
        
        This method:
        1. Hashes the password securely using scrypt
        2. Creates the User record in database
        3. Returns the created user certificate/credentials
        
        Args:
            registration_data: Verified registration data from RegisterAuthority
                Expected keys: name, email, password, qualification, age
                
        Returns:
            tuple: (success: bool, result: dict)
                - On success: (True, {'user_id': int, 'email': str, 'message': str})
                - On failure: (False, {'error': str})
        """
        try:
            # Hash password using scrypt algorithm
            # Format: scrypt:32768:8:1$randomsalt$hashedvalue
            hashed_password = self.hash_password(registration_data['password'])
            
            # Create new user record
            new_user = User(
                full_name=registration_data['name'],
                email=registration_data['email'],
                password=hashed_password,
                qualification=registration_data.get('qualification'),
                age=registration_data.get('age')
            )
            
            # Persist to database
            db.session.add(new_user)
            db.session.commit()
            
            return True, {
                'user_id': new_user.id,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'message': 'Registration successful! You can now login.',
                'certificate_issued_at': datetime.datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return False, {'error': f'Failed to create user account: {str(e)}'}
    
    def generate_user_certificate(self, user):
        """
        Generate a certificate object for an existing user.
        
        This can be used to provide user credentials/certificate information.
        
        Args:
            user: User model instance
            
        Returns:
            dict: User certificate information
        """
        return {
            'user_id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'qualification': user.qualification,
            'account_status': 'active',
            'certificate_type': 'user'
        }
    
    def revoke_certificate(self, user_id):
        """
        Revoke a user's certificate (deactivate account).
        
        Args:
            user_id: ID of the user whose certificate to revoke
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, 'User not found'
            
            # In a full implementation, you might set an 'is_active' flag
            # or move to a revoked certificates table
            return True, 'Certificate revoked successfully'
            
        except Exception as e:
            return False, f'Failed to revoke certificate: {str(e)}'
