from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from database.database_setup import get_db_session
from database.models import User
from config import Config
from logger import logger, log_error

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorator to check valid token is present"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
                
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            
            with get_db_session() as session:
                current_user = session.query(User).filter_by(id=data['user_id']).first()
                if not current_user:
                    return jsonify({'message': 'User not found'}), 401
                    
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        except Exception as e:
            log_error("TOKEN_VALIDATION_ERROR", str(e))
            return jsonify({'message': 'Token validation failed'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        with get_db_session() as session:
            # Check if user already exists
            if session.query(User).filter(
                (User.username == data['username']) | 
                (User.email == data['email'])
            ).first():
                return jsonify({'message': 'Username or email already exists'}), 409
                
            # Create new user
            new_user = User(
                username=data['username'],
                email=data['email'],
                password_hash=generate_password_hash(data['password']),
                api_key=data.get('api_key'),
                api_secret=data.get('api_secret'),
                created_at=datetime.utcnow()
            )
            
            session.add(new_user)
            session.commit()
            
            logger.info(f"New user registered: {data['username']}")
            
            return jsonify({
                'message': 'User registered successfully',
                'user_id': new_user.id
            }), 201
            
    except Exception as e:
        log_error("REGISTRATION_ERROR", str(e))
        return jsonify({'message': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return token"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Missing username or password'}), 400
            
        with get_db_session() as session:
            user = session.query(User).filter_by(username=data['username']).first()
            
            if not user or not check_password_hash(user.password_hash, data['password']):
                return jsonify({'message': 'Invalid username or password'}), 401
                
            # Generate token
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, Config.JWT_SECRET_KEY)
            
            # Update last login
            user.last_login = datetime.utcnow()
            session.commit()
            
            logger.info(f"User logged in: {user.username}")
            
            return jsonify({
                'token': token,
                'user_id': user.id,
                'username': user.username,
                'expires_in': 24 * 3600  # 24 hours in seconds
            }), 200
            
    except Exception as e:
        log_error("LOGIN_ERROR", str(e))
        return jsonify({'message': 'Login failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get user profile information"""
    try:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat(),
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }), 200
        
    except Exception as e:
        log_error("PROFILE_FETCH_ERROR", str(e))
        return jsonify({'message': 'Failed to fetch profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    try:
        data = request.get_json()
        
        with get_db_session() as session:
            user = session.query(User).get(current_user.id)
            
            # Update fields if provided
            if 'email' in data:
                user.email = data['email']
            if 'api_key' in data:
                user.api_key = data['api_key']
            if 'api_secret' in data:
                user.api_secret = data['api_secret']
            if 'password' in data:
                user.password_hash = generate_password_hash(data['password'])
                
            session.commit()
            
            logger.info(f"Profile updated for user: {user.username}")
            
            return jsonify({'message': 'Profile updated successfully'}), 200
            
    except Exception as e:
        log_error("PROFILE_UPDATE_ERROR", str(e))
        return jsonify({'message': 'Failed to update profile'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Log out user (client should discard token)"""
    try:
        logger.info(f"User logged out: {current_user.username}")
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        log_error("LOGOUT_ERROR", str(e))
        return jsonify({'message': 'Logout failed'}), 500

# Error handlers
@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Bad request'}), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'message': 'Unauthorized'}), 401

@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Not found'}), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    log_error("INTERNAL_SERVER_ERROR", str(error))
    return jsonify({'message': 'Internal server error'}), 500
