from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dao.order_dao import OrderDAO
from dao.item_dao import OrderItemDAO
from dao.customer_dao import CustomerDAO
from dao.agent_dao import AgentDAO
from dao.user_dao import UserDAO

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

@stats_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_order_stats():
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    user = UserDAO.get_by_id(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Get basic order statistics
    stats = OrderDAO.get_statistics()
    
    # Get recent orders
    recent_orders = OrderDAO.get_recent_orders(limit=5)
    
    return jsonify({
        'statistics': stats,
        'recent_orders': [order.to_dict() for order in recent_orders]
    }), 200

@stats_bp.route('/popular-items', methods=['GET'])
@jwt_required()
def get_popular_items():
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    user = UserDAO.get_by_id(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    popular_items = OrderItemDAO.get_popular_items(limit=10)
    
    # Transform raw query results into a dictionary
    items_data = [
        {'product_name': item[0], 'total_quantity': item[1]}
        for item in popular_items
    ]
    
    return jsonify(items_data), 200