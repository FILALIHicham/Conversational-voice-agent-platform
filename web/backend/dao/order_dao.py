from models.order import Order
from models.item import OrderItem
from extensions import db
from datetime import datetime

class OrderDAO:
    @staticmethod
    def create(customer_id, total_amount=0.0, status='Preparation'):
        """Create a new order"""
        order = Order(
            customer_id=customer_id,
            total_amount=total_amount,
            status=status
        )
        db.session.add(order)
        db.session.commit()
        return order
    
    @staticmethod
    def get_by_id(order_id):
        """Get order by ID"""
        return Order.query.get(order_id)
    
    @staticmethod
    def get_by_customer_id(customer_id):
        """Get all orders for a customer"""
        return Order.query.filter_by(customer_id=customer_id).all()
    
    @staticmethod
    def get_by_status(status):
        """Get all orders with a specific status"""
        return Order.query.filter_by(status=status).all()
    
    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Get orders created within a date range"""
        return Order.query.filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).all()
    
    @staticmethod
    def get_all():
        """Get all orders"""
        return Order.query.all()
    
    @staticmethod
    def update(order_id, data):
        """Update order information"""
        order = Order.query.get(order_id)
        if not order:
            return None
        
        if 'status' in data:
            order.status = data['status']
        if 'total_amount' in data:
            order.total_amount = data['total_amount']
        
        db.session.commit()
        return order
    
    @staticmethod
    def update_status(order_id, status):
        """Update just the order status"""
        order = Order.query.get(order_id)
        if not order:
            return None
        
        order.status = status
        db.session.commit()
        return order
    
    @staticmethod
    def delete(order_id):
        """Delete an order"""
        order = Order.query.get(order_id)
        if not order:
            return False
        
        db.session.delete(order)
        db.session.commit()
        return True
    
    @staticmethod
    def add_item(order_id, product_name, price, quantity=1):
        """Add an item to an order"""
        order = Order.query.get(order_id)
        if not order:
            return None
        
        item = OrderItem(
            product_name=product_name,
            price=price,
            quantity=quantity,
            order_id=order_id
        )
        
        # Update the order total
        order.total_amount += price * quantity
        
        db.session.add(item)
        db.session.commit()
        return item
    
    @staticmethod
    def remove_item(item_id):
        """Remove an item from an order"""
        item = OrderItem.query.get(item_id)
        if not item:
            return False
        
        # Update the order total
        order = Order.query.get(item.order_id)
        if order:
            order.total_amount -= item.price * item.quantity
        
        db.session.delete(item)
        db.session.commit()
        return True
    
    @staticmethod
    def get_recent_orders(limit=10):
        """Get the most recent orders"""
        return Order.query.order_by(Order.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_statistics():
        """Get order statistics"""
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='Preparation').count()
        completed_orders = Order.query.filter_by(status='Completed').count()
        
        return {
            'total': total_orders,
            'pending': pending_orders,
            'completed': completed_orders
        }