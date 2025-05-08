from models.customer import Customer
from extensions import db

class CustomerDAO:
    @staticmethod
    def create(phone_number, agent_id, name=None, address=None):
        """Create a new customer"""
        customer = Customer(
            phone_number=phone_number,
            agent_id=agent_id,
            name=name,
            address=address
        )
        db.session.add(customer)
        db.session.commit()
        return customer
    
    @staticmethod
    def get_by_id(customer_id):
        """Get customer by ID"""
        return Customer.query.get(customer_id)
    
    @staticmethod
    def get_by_phone_number(phone_number):
        """Get customer by phone number"""
        return Customer.query.filter_by(phone_number=phone_number).first()
    
    @staticmethod
    def get_by_agent_id(agent_id):
        """Get all customers for an agent"""
        return Customer.query.filter_by(agent_id=agent_id).all()
    
    @staticmethod
    def get_all():
        """Get all customers"""
        return Customer.query.all()
    
    @staticmethod
    def update(customer_id, data):
        """Update customer information"""
        customer = Customer.query.get(customer_id)
        if not customer:
            return None
        
        if 'phone_number' in data:
            customer.phone_number = data['phone_number']
        if 'name' in data:
            customer.name = data['name']
        if 'address' in data:
            customer.address = data['address']
        if 'agent_id' in data:
            customer.agent_id = data['agent_id']
        
        db.session.commit()
        return customer
    
    @staticmethod
    def delete(customer_id):
        """Delete a customer"""
        customer = Customer.query.get(customer_id)
        if not customer:
            return False
        
        db.session.delete(customer)
        db.session.commit()
        return True