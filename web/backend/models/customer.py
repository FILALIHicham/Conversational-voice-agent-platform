from extensions import db 
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)

    # Foreign Keys
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, phone_number, agent_id, name=None, address=None):
        self.phone_number = phone_number
        self.agent_id = agent_id
        self.name = name
        self.address = address
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'name': self.name,
            'address': self.address,
            'agent_id': self.agent_id
        }
    
    def __repr__(self):
        return f'<Customer {self.phone_number}>'

    # Getter and setter methods remain the same...
    def get_phone_number(self):
        return self.phone_number

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_address(self):
        return self.address

    def set_address(self, address):
        self.address = address

    def get_agent_id(self):
        return self.agent_id

    def set_agent_id(self, agent_id):
        self.agent_id = agent_id