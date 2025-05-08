from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dao.customer_dao import CustomerDAO
from dao.agent_dao import AgentDAO

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

# Route to create a customer for a specific agent
@customers_bp.route('/agent/<int:agent_id>', methods=['POST'])
@jwt_required()
def create_customer(agent_id):
    # Verify agent exists and belongs to user
    agent = AgentDAO.get_by_id(agent_id)
    if not agent:
        return jsonify({'message': 'Agent not found'}), 404
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or 'phone_number' not in data:
        return jsonify({'message': 'Phone number is required'}), 400
    
    # Check if phone number already exists for this agent
    existing_customer = CustomerDAO.get_by_phone_number(data['phone_number'])
    if existing_customer and existing_customer.agent_id == agent_id:
        return jsonify({'message': 'Phone number already registered for this agent'}), 409
    
    # Create customer
    try:
        customer = CustomerDAO.create(
            phone_number=data['phone_number'],
            agent_id=agent_id,
            name=data.get('name'),
            address=data.get('address')
        )
        
        return jsonify({
            'message': 'Customer created successfully',
            'customer': customer.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': f'Error creating customer: {str(e)}'}), 500

# Route to get all customers for a specific agent
@customers_bp.route('/agent/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_agent_customers(agent_id):
    # Verify agent exists and belongs to user
    agent = AgentDAO.get_by_id(agent_id)
    if not agent:
        return jsonify({'message': 'Agent not found'}), 404
    
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    customers = CustomerDAO.get_by_agent_id(agent_id)
    
    return jsonify([customer.to_dict() for customer in customers]), 200

# Route to get a specific customer
@customers_bp.route('/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
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
    
    return jsonify(customer.to_dict()), 200

# Route to update a customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
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
    updated_customer = CustomerDAO.update(customer_id, data)
    
    return jsonify({
        'message': 'Customer updated successfully',
        'customer': updated_customer.to_dict()
    }), 200

# Route to delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
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
    
    success = CustomerDAO.delete(customer_id)
    
    return jsonify({'message': 'Customer deleted successfully'}), 200