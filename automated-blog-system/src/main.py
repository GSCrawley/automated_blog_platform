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
    app = Flask(__name__, static_folder='../../blog-frontend/dist', static_url_path='/')
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
    
    # Register blueprints
    from src.routes.user import user_bp
    from src.routes.blog import blog_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(blog_bp, url_prefix='/api/blog')
    
    # Create tables
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")

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
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
