import os
import sys
import logging


# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    # Set static_folder to the built React app directory
    app = Flask(__name__, static_folder='../static', static_url_path='/')
    app.config.from_object(Config)
    Config.init_app(app)
    
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
    
    try:
        from src.routes.automation import automation_bp
        app.register_blueprint(automation_bp, url_prefix='/api/automation')
        print("✅ Automation blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering automation blueprint: {e}")
    
    # Serve React Frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

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

    app.run(host='0.0.0.0', port=5000, debug=False)
