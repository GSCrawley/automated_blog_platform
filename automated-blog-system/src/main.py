import os
import sys
import logging


# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
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
    from src.models.agent_models import AgentState, BlogInstance, AgentTask, AgentDecision
    
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
        from src.routes.agent_routes import agent_bp
        app.register_blueprint(agent_bp, url_prefix='/api/agents')
        print("✅ Agent blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering agent blueprint: {e}")

    try:
        from src.routes.automation import automation_bp
        app.register_blueprint(automation_bp, url_prefix='/api/automation')
        print("✅ Automation blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering automation blueprint: {e}")
    
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
    
    # Import db from models
    from src.models.user import db
    
    # Create tables
    with app.app_context():
        from src.models.user import db
        db.create_all()
        logger.info("Database initialized successfully")

    app.run(host='0.0.0.0', port=5000, debug=False)
    # Route to serve the main index.html for the React app
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')

    # Route to handle all other routes for React routing (e.g., /niches, /products)
    @app.errorhandler(404)
    def not_found(e):
        # Check if the request is for an API endpoint
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not Found', 'success': False}), 404
        # Otherwise, serve the index.html for React routing
        return send_from_directory(app.static_folder, 'index.html')

        return app

if __name__ == '__main__':
    flask_app = create_app()

    # Create tables
    from src.models.user import db
    with flask_app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")

    flask_app.run(host='0.0.0.0', port=5000, debug=False)
