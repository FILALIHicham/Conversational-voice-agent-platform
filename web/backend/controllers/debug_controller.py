from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/token', methods=['GET'])
@jwt_required()
def debug_token():
    """Endpoint to debug JWT token issues"""
    try:
        # Get identity and token data
        identity = get_jwt_identity()
        token_data = get_jwt()
        
        return jsonify({
            'identity': identity,
            'identity_type': str(type(identity)),
            'token_data': token_data
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': str(type(e))
        }), 500