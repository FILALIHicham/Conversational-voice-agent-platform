from extensions import db 
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='Preparation')  # Preparation, Out for Delivery, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, customer_id, total_amount=0.0, status='Preparation'):
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.status = status
    
    def to_dict(self, with_items=True):
        result = {
            'id': self.id,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'customer_id': self.customer_id,
        }
        
        if with_items:
            result['items'] = [item.to_dict() for item in self.items]
            
        return result
    
    def __repr__(self):
        return f'<Order {self.id}>'
    
    # Getters and setters remain the same...
    def get_id(self):
        return self.id

    def get_total_amount(self):
        return self.total_amount

    def get_status(self):
        return self.status

    def get_created_at(self):
        return self.created_at

    def get_customer_id(self):
        return self.customer_id

    def get_items(self):
        return self.items.all()

    # Setters
    def set_total_amount(self, total_amount):
        self.total_amount = total_amount

    def set_status(self, status):
        self.status = status

    def set_customer_id(self, customer_id):
        self.customer_id = customer_id