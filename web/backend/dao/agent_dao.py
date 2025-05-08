from models.agent import Agent
from extensions import db
import uuid

class AgentDAO:
    @staticmethod
    def create(name, user_id, system_prompt, voice='af_heart', knowledge=None, speed=1.0, min_silence=500, api_key=None):
        """Create a new agent"""
        agent = Agent(
            name=name,
            user_id=user_id,
            system_prompt=system_prompt,
            voice=voice,
            knowledge=knowledge,
            speed=speed,
            min_silence=min_silence
        )
        
        # The Agent constructor already sets a UUID, but we allow override
        if api_key:
            agent.api_key = api_key
            
        db.session.add(agent)
        db.session.commit()
        return agent
    
    @staticmethod
    def get_by_id(agent_id):
        """Get agent by ID"""
        return Agent.query.get(agent_id)
    
    @staticmethod
    def get_by_api_key(api_key):
        """Get agent by API key"""
        return Agent.query.filter_by(api_key=api_key).first()
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get all agents for a user"""
        return Agent.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_all():
        """Get all agents"""
        return Agent.query.all()
    
    @staticmethod
    def update(agent_id, data):
        """Update agent information"""
        agent = Agent.query.get(agent_id)
        if not agent:
            return None
        
        if 'name' in data:
            agent.name = data['name']
        if 'voice' in data:
            agent.voice = data['voice']
        if 'knowledge' in data:
            agent.knowledge = data['knowledge']
        if 'system_prompt' in data:
            agent.system_prompt = data['system_prompt']
        if 'speed' in data:
            agent.speed = data['speed']
        if 'min_silence' in data:
            agent.min_silence = data['min_silence']
        if 'api_key' in data:
            agent.api_key = data['api_key']
        
        db.session.commit()
        return agent
    
    @staticmethod
    def regenerate_api_key(agent_id):
        """Generate a new API key for the agent"""
        agent = Agent.query.get(agent_id)
        if not agent:
            return None
        
        agent.api_key = str(uuid.uuid4())
        db.session.commit()
        return agent
    
    @staticmethod
    def delete(agent_id):
        """Delete an agent"""
        try:
            print(f"AgentDAO: Attempting to delete agent with ID {agent_id}")
            agent = Agent.query.get(agent_id)
            
            if not agent:
                print(f"AgentDAO: Agent with ID {agent_id} not found")
                return False
            
            print(f"AgentDAO: Found agent {agent.name}, deleting from database")
            db.session.delete(agent)
            db.session.commit()
            print(f"AgentDAO: Successfully deleted agent with ID {agent_id}")
            return True
            
        except Exception as e:
            print(f"AgentDAO: Error deleting agent: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def validate_api_key(api_key):
        """Check if an API key is valid"""
        agent = Agent.query.filter_by(api_key=api_key).first()
        return agent is not None