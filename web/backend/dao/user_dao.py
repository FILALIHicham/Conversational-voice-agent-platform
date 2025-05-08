from models.user import User
from extensions import db

class UserDAO:
    @staticmethod
    def create(username, email, password):
        """Create a new user"""
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_all():
        """Get all users"""
        return User.query.all()
    
    @staticmethod
    def update(user_id, data):
        """Update user information"""
        user = User.query.get(user_id)
        if not user:
            return None
        
        # Use the setter methods for better encapsulation
        if 'username' in data and data['username']:
            user.set_username(data['username'])
            
        if 'email' in data and data['email']:
            user.set_email(data['email'])
            
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        return user
    
    @staticmethod
    def delete(user_id):
        """Delete a user"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        db.session.delete(user)
        db.session.commit()
        return True