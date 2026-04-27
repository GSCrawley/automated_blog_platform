import os
import sys
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Add core directory to path for agent imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
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

    # Import models (ensures tables are created and visible to Alembic autogenerate)
    from src.models.product import Product, Article
    from src.models.niche import Niche
    from src.models.agent_models import AgentState, BlogInstance, AgentTask, AgentDecision
    from src.models.observability import CostEvent, Budget, EditorialReport  # PR #3

    # Initialize Flask-Migrate (PR #3). The migrations/ directory lives at
    # automated-blog-system/migrations/ — relative to the working dir set by
    # FLASK_APP=src.main:create_app.
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "migrations",
    )
    Migrate(app, db, directory=migrations_dir)

    # Initialize Agent Manager (attached to app for route access)
    try:
        # Import from core directory (relative to project root)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        core_agents_path = os.path.join(project_root, 'core')
        if core_agents_path not in sys.path:
            sys.path.insert(0, core_agents_path)

        from agents.agent_manager import AgentManager
        app.agent_manager = AgentManager(
            redis_host=app.config.get('REDIS_HOST', 'localhost'),
            redis_port=app.config.get('REDIS_PORT', 6379)
        )
        print("✅ Agent Manager initialized successfully")

        # Start agents in a background thread so they run alongside Flask
        import threading
        agent_thread = threading.Thread(
            target=app.agent_manager.start_monitoring_loop,
            name="AgentManagerMonitor",
            daemon=True
        )
        agent_thread.start()
        print("✅ Agent system started in background")
    except Exception as e:
        print(f"⚠️ Agent Manager initialization failed: {e}")
        print("   Agent routes will use mock data fallback")
        app.agent_manager = None

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
        from src.routes.publisher import publisher_bp
        app.register_blueprint(publisher_bp, url_prefix='/api/publisher')
        print("✅ Publisher blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering publisher blueprint: {e}")

    try:
        from src.routes.budget import budget_bp
        app.register_blueprint(budget_bp, url_prefix='/api/budget')
        print("✅ Budget blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering budget blueprint: {e}")


    # Serve React Frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    # Error handler for 404 - serve React app for non-API routes
    @app.errorhandler(404)
    def not_found(e):
        # Check if the request is for an API endpoint
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not Found', 'success': False}), 404
        # Otherwise, serve the index.html for React routing
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
        db.create_all()
        logger.info("Database initialized successfully")

    # Start the Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)
