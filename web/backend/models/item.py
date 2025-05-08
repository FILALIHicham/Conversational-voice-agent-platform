from extensions import db 

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    
    # Foreign Keys
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    def __init__(self, product_name, price, order_id, quantity=1, notes=None):
        self.product_name = product_name
        self.price = price
        self.order_id = order_id
        self.quantity = quantity
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price,
            'order_id': self.order_id,
            'subtotal': self.price * self.quantity
        }
    
    def __repr__(self):
        return f'<OrderItem {self.product_name} x{self.quantity}>'
    
    # Getters and setters remain the same...
    def get_id(self):
        return self.id

    def get_product_name(self):
        return self.product_name

    def get_quantity(self):
        return self.quantity

    def get_price(self):
        return self.price

    def get_order_id(self):
        return self.order_id

    def get_subtotal(self):
        return self.price * self.quantity

    # Setters
    def set_product_name(self, product_name):
        self.product_name = product_name

    def set_quantity(self, quantity):
        self.quantity = quantity

    def set_price(self, price):
        self.price = price

    def set_order_id(self, order_id):
        self.order_id = order_id