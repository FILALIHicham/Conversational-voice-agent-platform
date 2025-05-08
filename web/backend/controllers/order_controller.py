from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dao.order_dao import OrderDAO
from dao.customer_dao import CustomerDAO
from dao.agent_dao import AgentDAO

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# Route to create an order for a specific customer
@orders_bp.route('/customer/<int:customer_id>', methods=['POST'])
@jwt_required()
def create_order(customer_id):
    # Verify customer exists
    customer = CustomerDAO.get_by_id(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404
    
    # Verify the customer's agent belongs to the user
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    # Create order
    try:
        order = OrderDAO.create(
            customer_id=customer_id,
            total_amount=data.get('total_amount', 0.0),
            status=data.get('status', 'Preparation')
        )
        
        # Add items if provided
        if 'items' in data and isinstance(data['items'], list):
            for item_data in data['items']:
                if 'product_name' in item_data and 'price' in item_data:
                    OrderDAO.add_item(
                        order_id=order.id,
                        product_name=item_data['product_name'],
                        price=item_data['price'],
                        quantity=item_data.get('quantity', 1)
                    )
        
        # Refresh order to get updated total and items
        order = OrderDAO.get_by_id(order.id)
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': f'Error creating order: {str(e)}'}), 500

# Route to get all orders for a specific customer
@orders_bp.route('/customer/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer_orders(customer_id):
    # Verify customer exists
    customer = CustomerDAO.get_by_id(customer_id)
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404
    
    # Verify the customer's agent belongs to the user
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    orders = OrderDAO.get_by_customer_id(customer_id)
    
    return jsonify([order.to_dict() for order in orders]), 200

# Route to get a specific order
@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    order = OrderDAO.get_by_id(order_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Verify the order's customer's agent belongs to the user
    customer = CustomerDAO.get_by_id(order.customer_id)
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    return jsonify(order.to_dict()), 200

# Route to update an order
@orders_bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    order = OrderDAO.get_by_id(order_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Verify the order's customer's agent belongs to the user
    customer = CustomerDAO.get_by_id(order.customer_id)
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    updated_order = OrderDAO.update(order_id, data)
    
    return jsonify({
        'message': 'Order updated successfully',
        'order': updated_order.to_dict()
    }), 200

# Route to update just the order status
@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    order = OrderDAO.get_by_id(order_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Verify the order's customer's agent belongs to the user
    customer = CustomerDAO.get_by_id(order.customer_id)
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'message': 'Status is required'}), 400
    
    updated_order = OrderDAO.update_status(order_id, data['status'])
    
    return jsonify({
        'message': 'Order status updated successfully',
        'order': updated_order.to_dict()
    }), 200

# Route to delete an order
@orders_bp.route('/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    order = OrderDAO.get_by_id(order_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Verify the order's customer's agent belongs to the user
    customer = CustomerDAO.get_by_id(order.customer_id)
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    success = OrderDAO.delete(order_id)
    
    return jsonify({'message': 'Order deleted successfully'}), 200

# Route to add an item to an order
@orders_bp.route('/<int:order_id>/items', methods=['POST'])
@jwt_required()
def add_order_item(order_id):
    order = OrderDAO.get_by_id(order_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Verify the order's customer's agent belongs to the user
    customer = CustomerDAO.get_by_id(order.customer_id)
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not all(k in data for k in ('product_name', 'price')):
        return jsonify({'message': 'Product name and price are required'}), 400
    
    # Add item
    try:
        item = OrderDAO.add_item(
            order_id=order_id,
            product_name=data['product_name'],
            price=data['price'],
            quantity=data.get('quantity', 1)
        )
        
        return jsonify({
            'message': 'Item added successfully',
            'item': item.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': f'Error adding item: {str(e)}'}), 500

# Route to remove an item from an order
@orders_bp.route('/<int:order_id>/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_order_item(order_id, item_id):
    order = OrderDAO.get_by_id(order_id)
    
    if not order:
        return jsonify({'message': 'Order not found'}), 404
    
    # Verify the order's customer's agent belongs to the user
    customer = CustomerDAO.get_by_id(order.customer_id)
    agent = AgentDAO.get_by_id(customer.agent_id)
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    success = OrderDAO.remove_item(item_id)
    
    if not success:
        return jsonify({'message': 'Item not found'}), 404
    
    return jsonify({'message': 'Item removed successfully'}), 200