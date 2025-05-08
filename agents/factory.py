import os
import yaml
import json
import logging
from typing import Dict, List, Optional, Any
import uuid

from agents.agent import VoiceAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_factory")

class AgentFactory:
    """Factory for creating and managing voice agents"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize agent factory
        
        Args:
            config_dir: Directory containing agent configurations
        """
        self.config_dir = config_dir
        
        # Default service endpoints
        self.default_endpoints = {
            "asr_url": "ws://localhost:8002/ws",
            "llm_url": "http://localhost:8000",
            "tts_url": "http://localhost:8001"
        }
        
        # Default extraction configuration
        self.default_extraction_config = {
            "base_url": "https://api.scaleway.ai/1487912f-76d4-4899-a8b3-1dbf08366f7c/v1",
            "model": "deepseek-r1-distill-llama-70b"
        }
        
        # Active agents
        self.agents: Dict[str, VoiceAgent] = {}
        
        logger.info(f"Agent factory initialized with config_dir={config_dir}")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load agent configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            return {}
            
        try:
            # Determine file type from extension
            _, ext = os.path.splitext(config_path)
            
            if ext.lower() == '.yaml' or ext.lower() == '.yml':
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            elif ext.lower() == '.json':
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                logger.error(f"Unsupported configuration file format: {ext}")
                return {}
                
            logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def create_agent(self, 
                   config: Dict[str, Any] = None, 
                   config_path: str = None,
                   agent_id: str = None) -> Optional[VoiceAgent]:
        """
        Create a voice agent from configuration
        
        Args:
            config: Configuration dictionary (optional)
            config_path: Path to configuration file (optional)
            agent_id: Agent ID (optional, will be generated if not provided)
            
        Returns:
            Voice agent instance
        """
        # Generate agent ID if not provided
        if not agent_id:
            agent_id = str(uuid.uuid4())
            
        # Load configuration from file if provided
        if config_path and not config:
            config = self.load_config(config_path)
            
        # Use empty config if none provided
        if not config:
            config = {}
            
        # Get service endpoints
        asr_url = config.get('asr_url', self.default_endpoints['asr_url'])
        llm_url = config.get('llm_url', self.default_endpoints['llm_url'])
        tts_url = config.get('tts_url', self.default_endpoints['tts_url'])
        
        # Get agent configuration
        system_prompt = config.get('system_prompt')
        
        # Get system prompt from file if path provided
        system_prompt_path = config.get('system_prompt_path')
        if system_prompt_path and not system_prompt:
            try:
                with open(system_prompt_path, 'r') as f:
                    system_prompt = f.read()
            except Exception as e:
                logger.error(f"Error reading system prompt file: {e}")
        
        knowledge = config.get('knowledge')
        
        # Get knowledge from file if path provided
        knowledge_path = config.get('knowledge_path')
        if knowledge_path and not knowledge:
            try:
                with open(knowledge_path, 'r') as f:
                    knowledge = f.read()
            except Exception as e:
                logger.error(f"Error reading knowledge file: {e}")
        
        # Get TTS configuration
        tts_config = config.get('tts', {})
        tts_voice = tts_config.get('voice', 'af_heart')
        tts_speed = tts_config.get('speed', 1.0)
        
        # Get VAD configuration
        vad_config = config.get('vad', {})
        
        # Get order extraction configuration
        extraction_config_raw = config.get('extraction', {})
        
        # Merge with default extraction configuration
        extraction_config = self.default_extraction_config.copy()
        extraction_config.update(extraction_config_raw)
        
        # Extract order extraction API key
        api_key = extraction_config.get('api_key')
        
        # Try to get API key from environment variable if not in config
        if not api_key:
            api_key_env_var = extraction_config.get('api_key_env_var')
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
                
            if not api_key:
                logger.warning("No API key provided for order extraction")
        
        # Set the API key in the extraction config
        extraction_config['api_key'] = api_key
        
        # Create the agent
        agent = VoiceAgent(
            agent_id=agent_id,
            asr_url=asr_url,
            llm_url=llm_url,
            tts_url=tts_url,
            system_prompt=system_prompt,
            knowledge=knowledge,
            tts_voice=tts_voice,
            tts_speed=tts_speed,
            vad_config=vad_config,
            extraction_config=extraction_config
        )
        
        # Store the agent
        self.agents[agent_id] = agent
        
        logger.info(f"Created agent {agent_id}")
        return agent
    
    def create_agent_from_file(self, config_path: str, agent_id: str = None) -> Optional[VoiceAgent]:
        """
        Create a voice agent from configuration file
        
        Args:
            config_path: Path to configuration file
            agent_id: Agent ID (optional)
            
        Returns:
            Voice agent instance
        """
        return self.create_agent(config_path=config_path, agent_id=agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[VoiceAgent]:
        """
        Get agent by ID
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Voice agent instance
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """
        Get list of agent IDs
        
        Returns:
            List of agent IDs
        """
        return list(self.agents.keys())
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove agent by ID
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Success flag
        """
        if agent_id not in self.agents:
            return False
            
        # Get agent
        agent = self.agents[agent_id]
        
        # Remove from dictionary
        del self.agents[agent_id]
        
        logger.info(f"Removed agent {agent_id}")
        return True
    
    def list_available_configs(self) -> List[str]:
        """
        List available configuration files
        
        Returns:
            List of configuration file names
        """
        if not self.config_dir or not os.path.exists(self.config_dir):
            return []
            
        # Find all YAML and JSON files
        configs = []
        for file in os.listdir(self.config_dir):
            if file.endswith('.yaml') or file.endswith('.yml') or file.endswith('.json'):
                configs.append(file)
                
        return configs
    
    def get_extracted_order(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the extracted order information for an agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Extracted order information or None
        """
        agent = self.agents.get(agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not found")
            return None
            
        return agent.extracted_order
    
    async def finish_conversation(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Finish the conversation for an agent and extract order information
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Extracted order information or None
        """
        agent = self.agents.get(agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not found")
            return None
            
        # Finish conversation and extract order
        await agent.finish_conversation()
        
        # Return the extracted order
        return agent.extracted_order