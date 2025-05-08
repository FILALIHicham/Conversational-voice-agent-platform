from app import create_app, db
from models.user import User
from models.agent import Agent
from models.customer import Customer
from models.order import Order
from models.item import OrderItem

def init_db():
    """Initialize the database and create tables"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        
        print("Database initialized successfully")

if __name__ == '__main__':
    init_db()