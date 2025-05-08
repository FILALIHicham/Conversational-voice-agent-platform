from extensions import db 
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationship - Define relationship but use string for Agent to avoid circular imports
    agents = db.relationship('Agent', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin

    # Getters
    def get_id(self):
        return self.id
    
    def get_username(self):
        return self.username
    
    def get_email(self):
        return self.email
    
    # Setters
    def set_username(self, username):
        self.username = username
        
    def set_email(self, email):
        self.email = email
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    # Password verification
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin
        }
    
    def __repr__(self):
        return f'<User {self.username}>'