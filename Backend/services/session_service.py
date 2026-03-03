"""
Session Service
================
Handles authenticated session creation and management after successful login verification.

This service is responsible for:
1. Creating JWT tokens for authenticated sessions
2. Managing session expiration and refresh
3. Building identity claims for different roles
4. Handling session invalidation/logout

Flow:
    LoginChecker (verified) -> SessionService (create session) -> JWT Token returned
"""

import datetime
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity


class SessionService:
    """
    Session Service creates and manages authenticated sessions.
    
    After LoginChecker has verified credentials, this service:
    - Creates JWT access tokens with appropriate claims
    - Sets session expiration based on role
    - Builds identity payloads for different user types
    """
    
    ACCESS_TOKEN_DURATION = datetime.timedelta(minutes=15)
    REFRESH_TOKEN_DURATION = datetime.timedelta(minutes=120)
    
    def __init__(self):
        """Initialize the Session Service."""
        pass

    def _create_token_pair(self, identity, role):
        session_start = datetime.datetime.utcnow()
        additional_claims = {
            'role': role,
            'session_start': int(session_start.timestamp())
        }
        access_token = create_access_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=self.ACCESS_TOKEN_DURATION
        )
        refresh_token = create_refresh_token(
            identity=identity,
            additional_claims=additional_claims,
            expires_delta=self.REFRESH_TOKEN_DURATION
        )
        return access_token, refresh_token
    
    def create_admin_session(self):
        """
        Create an authenticated session for admin.
        
        Returns:
            dict: Session data including JWT token
        """
        # Admin identity is just the string 'admin'
        identity = 'admin'
        access_token, refresh_token = self._create_token_pair(identity, 'admin')
        
        return {
            'token': access_token,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'role': 'admin',
            'message': 'Admin login successful',
            'access_expires_in': self.ACCESS_TOKEN_DURATION.total_seconds(),
            'refresh_expires_in': self.REFRESH_TOKEN_DURATION.total_seconds()
        }
    
    def create_quiz_master_session(self, quiz_master_data):
        """
        Create an authenticated session for Quiz Master.
        
        Args:
            quiz_master_data: Dict containing quiz master info
                Expected keys: id, email, full_name
                
        Returns:
            dict: Session data including JWT token and user info
        """
        # Quiz Master identity includes role and user data
        identity = {
            'id': quiz_master_data['id'],
            'email': quiz_master_data['email'],
            'role': 'quiz_master',
            'full_name': quiz_master_data['full_name']
        }
        
        access_token, refresh_token = self._create_token_pair(identity, 'quiz_master')
        
        return {
            'token': access_token,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'role': 'quiz_master',
            'message': 'Quiz Master login successful',
            'full_name': quiz_master_data['full_name'],
            'access_expires_in': self.ACCESS_TOKEN_DURATION.total_seconds(),
            'refresh_expires_in': self.REFRESH_TOKEN_DURATION.total_seconds()
        }
    
    def create_user_session(self, user_data):
        """
        Create an authenticated session for regular User.
        
        Args:
            user_data: Dict containing user info
                Expected keys: id, email, full_name, qualification
                
        Returns:
            dict: Session data including JWT token and user info
        """
        # User identity includes role and user data
        identity = {
            'id': user_data['id'],
            'email': user_data['email'],
            'role': 'user',
            'qualification': user_data.get('qualification')
        }
        
        access_token, refresh_token = self._create_token_pair(identity, 'user')
        
        return {
            'token': access_token,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'role': 'user',
            'message': 'Login successful',
            'full_name': user_data['full_name'],
            'access_expires_in': self.ACCESS_TOKEN_DURATION.total_seconds(),
            'refresh_expires_in': self.REFRESH_TOKEN_DURATION.total_seconds()
        }
    
    def create_session(self, role, entity_data):
        """
        Create session based on role.
        
        Args:
            role: User role ('admin', 'quiz_master', 'user')
            entity_data: Data for the authenticated entity
            
        Returns:
            dict: Session data including JWT token
        """
        if role == 'admin':
            return self.create_admin_session()
        elif role == 'quiz_master':
            return self.create_quiz_master_session(entity_data)
        elif role == 'user':
            return self.create_user_session(entity_data)
        else:
            raise ValueError(f"Unknown role: {role}")
    
    def get_current_session_identity(self):
        """
        Get the identity from the current JWT token.
        
        Returns:
            str or dict: Identity payload from current token
        """
        return get_jwt_identity()
    
    def extend_session(self, current_identity):
        """
        Extend/refresh the current session with a new token.
        
        Args:
            current_identity: Current JWT identity payload
            
        Returns:
            dict: New session data with fresh token
        """
        if current_identity == 'admin':
            role = 'admin'
        elif isinstance(current_identity, dict):
            role = current_identity.get('role', 'user')
        else:
            role = 'user'

        access_token, refresh_token = self._create_token_pair(current_identity, role)
        
        return {
            'token': access_token,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'role': role,
            'message': 'Session extended',
            'access_expires_in': self.ACCESS_TOKEN_DURATION.total_seconds(),
            'refresh_expires_in': self.REFRESH_TOKEN_DURATION.total_seconds()
        }
    
    @staticmethod
    def build_identity_claims(role, entity):
        """
        Build identity claims for JWT token based on role and entity.
        
        Args:
            role: User role string
            entity: User/QuizMaster model instance or dict
            
        Returns:
            str or dict: Identity to encode in JWT
        """
        if role == 'admin':
            return 'admin'
        
        if isinstance(entity, dict):
            return {
                'id': entity.get('id'),
                'email': entity.get('email'),
                'role': role,
                'full_name': entity.get('full_name'),
                'qualification': entity.get('qualification')
            }
        
        # Handle model instances
        return {
            'id': entity.id,
            'email': entity.email,
            'role': role,
            'full_name': getattr(entity, 'full_name', None),
            'qualification': getattr(entity, 'qualification', None)
        }
