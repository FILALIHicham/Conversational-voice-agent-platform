from extensions import db 
from datetime import datetime
import uuid

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    voice = db.Column(db.String(50), nullable=False, default='af_heart')
    knowledge = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=False)
    speed = db.Column(db.Float, nullable=False, default=1.0)
    min_silence = db.Column(db.Integer, nullable=False, default=500) 
    api_key = db.Column(db.String(100), nullable=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships - Use string reference for Customer to avoid circular imports
    customers = db.relationship('Customer', backref='agent', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, name, user_id, system_prompt, voice='af_heart', knowledge=None, speed=1.0, min_silence=500):
        self.name = name
        self.user_id = user_id
        self.system_prompt = system_prompt
        self.voice = voice
        self.knowledge = knowledge
        self.speed = speed
        self.min_silence = min_silence
        self.api_key = str(uuid.uuid4()) 
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'voice': self.voice,
            'knowledge': self.knowledge,
            'system_prompt': self.system_prompt,
            'speed': self.speed,
            'min_silence': self.min_silence,
            'api_key': self.api_key,
            'user_id': self.user_id
        }
    
    def __repr__(self):
        return f'<Agent {self.name}>'
    
    # Getters and setters remain the same...
    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_voice(self):
        return self.voice

    def get_knowledge(self):
        return self.knowledge
        
    def get_api_key(self):
        return self.api_key
        
    def set_api_key(self, api_key):
        self.api_key = api_key

    def get_system_prompt(self):
        return self.system_prompt

    def get_speed(self):
        return self.speed

    def get_min_silence(self):
        return self.min_silence

    def get_user_id(self):
        return self.user_id

    # Setters
    def set_name(self, name):
        self.name = name

    def set_voice(self, voice):
        self.voice = voice

    def set_knowledge(self, knowledge):
        self.knowledge = knowledge

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt

    def set_speed(self, speed):
        self.speed = speed

    def set_min_silence(self, min_silence):
        self.min_silence = min_silence