from models.item import OrderItem
from extensions import db
from sqlalchemy import func

class OrderItemDAO:
    @staticmethod
    def create(product_name, price, order_id, quantity=1):
        """Create a new order item"""
        item = OrderItem(
            product_name=product_name,
            price=price,
            order_id=order_id,
            quantity=quantity
        )
        db.session.add(item)
        db.session.commit()
        return item
    
    @staticmethod
    def get_by_id(item_id):
        """Get item by ID"""
        return OrderItem.query.get(item_id)
    
    @staticmethod
    def get_by_order_id(order_id):
        """Get all items for an order"""
        return OrderItem.query.filter_by(order_id=order_id).all()
    
    @staticmethod
    def get_all():
        """Get all order items"""
        return OrderItem.query.all()
    
    @staticmethod
    def update(item_id, data):
        """Update item information"""
        item = OrderItem.query.get(item_id)
        if not item:
            return None
        
        old_subtotal = item.price * item.quantity
        
        if 'product_name' in data:
            item.product_name = data['product_name']
        if 'price' in data:
            item.price = data['price']
        if 'quantity' in data:
            item.quantity = data['quantity']
        
        # Update the order total if price or quantity changed
        new_subtotal = item.price * item.quantity
        if old_subtotal != new_subtotal:
            from models.order import Order
            order = Order.query.get(item.order_id)
            if order:
                order.total_amount = order.total_amount - old_subtotal + new_subtotal
        
        db.session.commit()
        return item
    
    @staticmethod
    def delete(item_id):
        """Delete an order item"""
        item = OrderItem.query.get(item_id)
        if not item:
            return False
        
        # Update the order total
        from models.order import Order
        order = Order.query.get(item.order_id)
        if order:
            order.total_amount -= item.price * item.quantity
        
        db.session.delete(item)
        db.session.commit()
        return True
    
    @staticmethod
    def get_popular_items(limit=5):
        """Get the most frequently ordered items"""
        
        # Group by product name and sum quantities
        results = db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).group_by(OrderItem.product_name).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(limit).all()
        
        return results