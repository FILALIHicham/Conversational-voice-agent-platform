from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dao.user_dao import UserDAO

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_all_users():
    # For a real app, should check if user is admin
    users = UserDAO.get_all()
    return jsonify([user.to_dict() for user in users]), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    # Check permissions (only allow users to view themselves or admins to view anyone)
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        # In a real app, check if current user is admin
        return jsonify({'message': 'Unauthorized access'}), 403
    
    user = UserDAO.get_by_id(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    # Check permissions (only allow users to update themselves)
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    updated_user = UserDAO.update(user_id, data)
    
    if not updated_user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'message': 'User updated successfully',
        'user': updated_user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    # Check permissions (only allow users to delete themselves)
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    success = UserDAO.delete(user_id)
    if not success:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({'message': 'User deleted successfully'}), 200