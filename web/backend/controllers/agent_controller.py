from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dao.agent_dao import AgentDAO
from dao.user_dao import UserDAO

agents_bp = Blueprint('agents', __name__, url_prefix='/agents')

@agents_bp.route('', methods=['POST'])
@jwt_required()
def create_agent():
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not all(k in data for k in ('name', 'system_prompt')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Create new agent
    try:
        agent = AgentDAO.create(
            name=data['name'],
            user_id=user_id,
            system_prompt=data['system_prompt'],
            voice=data.get('voice', 'af_heart'),
            knowledge=data.get('knowledge'),
            speed=data.get('speed', 1.0),
            min_silence=data.get('min_silence', 500)
        )
        return jsonify({
            'message': 'Agent created successfully',
            'agent': agent.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': f'Error creating agent: {str(e)}'}), 500

@agents_bp.route('', methods=['GET'])
@jwt_required()
def get_user_agents():
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
        
    agents = AgentDAO.get_by_user_id(user_id)
    
    return jsonify([agent.to_dict() for agent in agents]), 200

@agents_bp.route('/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_agent(agent_id):
    agent = AgentDAO.get_by_id(agent_id)
    
    if not agent:
        return jsonify({'message': 'Agent not found'}), 404
    
    # Check if the agent belongs to the current user
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
        
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    return jsonify(agent.to_dict()), 200

@agents_bp.route('/<int:agent_id>', methods=['PUT'])
@jwt_required()
def update_agent(agent_id):
    agent = AgentDAO.get_by_id(agent_id)
    
    if not agent:
        return jsonify({'message': 'Agent not found'}), 404
    
    # Check if the agent belongs to the current user
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
        
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    data = request.get_json()
    updated_agent = AgentDAO.update(agent_id, data)
    
    return jsonify({
        'message': 'Agent updated successfully',
        'agent': updated_agent.to_dict()
    }), 200

@agents_bp.route('/<int:agent_id>', methods=['DELETE'])
@jwt_required()
def delete_agent(agent_id):
    try:
        # Log the incoming request
        print(f"Attempting to delete agent with ID: {agent_id}")
        
        # Get and convert user ID
        user_id = get_jwt_identity()
        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
        
        print(f"Authenticated user ID: {user_id}")
        
        # Find the agent
        agent = AgentDAO.get_by_id(agent_id)
        
        if not agent:
            print(f"Agent with ID {agent_id} not found")
            return jsonify({'message': 'Agent not found'}), 404
        
        print(f"Agent found: {agent.name}, belongs to user: {agent.user_id}")
        
        # Check if the agent belongs to the current user
        if agent.user_id != user_id:
            print(f"Unauthorized: Agent belongs to user {agent.user_id}, not the authenticated user {user_id}")
            return jsonify({'message': 'Unauthorized access'}), 403
        
        # Delete the agent
        print(f"Deleting agent with ID: {agent_id}")
        success = AgentDAO.delete(agent_id)
        
        if not success:
            print(f"Failed to delete agent with ID: {agent_id}")
            return jsonify({'message': 'Error deleting agent'}), 500
        
        print(f"Successfully deleted agent with ID: {agent_id}")
        return jsonify({'message': 'Agent deleted successfully'}), 200
    
    except Exception as e:
        print(f"Exception in delete_agent: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@agents_bp.route('/<int:agent_id>/regenerate-key', methods=['POST'])
@jwt_required()
def regenerate_api_key(agent_id):
    agent = AgentDAO.get_by_id(agent_id)
    
    if not agent:
        return jsonify({'message': 'Agent not found'}), 404
    
    # Check if the agent belongs to the current user
    # IMPORTANT FIX: Get identity and convert to int if it's a string
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
        
    if agent.user_id != user_id:
        return jsonify({'message': 'Unauthorized access'}), 403
    
    updated_agent = AgentDAO.regenerate_api_key(agent_id)
    
    return jsonify({
        'message': 'API key regenerated successfully',
        'agent': updated_agent.to_dict()
    }), 200