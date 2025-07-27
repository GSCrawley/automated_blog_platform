import os
import sys
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from flask_cors import CORS
from src.config import Config


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)  # This will print the database path
    
    # Initialize database
    from src.models.user import db
    db.init_app(app)
    
    # Initialize CORS
    CORS(app)
    
    # Import models
    from src.models.product import Product, Article
    from src.models.niche import Niche
    
    # Register blueprints with debug prints
    try:
        from src.routes.user import user_bp
        app.register_blueprint(user_bp, url_prefix='/api/user')
        print("✅ User blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering user blueprint: {e}")
    
    try:
        from src.routes.blog import blog_bp
        app.register_blueprint(blog_bp, url_prefix='/api/blog')
        print("✅ Blog blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering blog blueprint: {e}")
    
     # Add this new block to register the automation blueprint
    try:
        from src.routes.automation import automation_bp
        app.register_blueprint(automation_bp, url_prefix='/api/automation')
        print("✅ Automation blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering automation blueprint: {e}")
    
    # Print all registered routes
    print("\n📋 Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.methods} {rule.rule}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create tables
    with app.app_context():
        from src.models.user import db
        db.create_all()
        logger.info("Database initialized successfully")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

