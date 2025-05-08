from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from dotenv import load_dotenv
from extensions import db, migrate, bcrypt

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database configuration
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'root')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'voiceagentplatform')
    
    # Create MySQL connection string
    db_port = os.environ.get('DB_PORT', '')
    
    if db_port:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    
    print(f"Using database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT Configuration - IMPORTANT FIX
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Initialize extensions with app
    CORS(app, origins="*", supports_credentials=True, allow_headers=[
        "Content-Type", "Authorization", "Access-Control-Allow-Credentials"
    ])
    app.config['CORS_HEADERS'] = 'Content-Type'
    
    # Add CORS after_request handler
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    
    # Initialize JWT with app
    jwt = JWTManager(app)
    
    # Import and register blueprints
    from controllers.auth_controller import auth_bp
    from controllers.user_controller import users_bp
    from controllers.agent_controller import agents_bp
    from controllers.customer_controller import customers_bp
    from controllers.order_controller import orders_bp
    from controllers.stats_controller import stats_bp
    from controllers.debug_controller import debug_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(debug_bp)  # Add debug blueprint
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)