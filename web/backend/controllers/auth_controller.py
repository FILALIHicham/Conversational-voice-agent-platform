from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from dao.user_dao import UserDAO

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if username or email already exists
    if UserDAO.get_by_username(data['username']):
        return jsonify({'message': 'Username already exists'}), 409
    
    if UserDAO.get_by_email(data['email']):
        return jsonify({'message': 'Email already exists'}), 409
    
    # Create new user
    try:
        user = UserDAO.create(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate required fields
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'message': 'Missing username or password'}), 400
    
    # Find user by username
    user = UserDAO.get_by_username(data['username'])
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    # IMPORTANT FIX: Create access token with string user ID
    # Convert user.id to string to ensure compatibility
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    # IMPORTANT FIX: Convert string ID back to integer if needed
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
        
    user = UserDAO.get_by_id(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200