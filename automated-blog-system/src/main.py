import os
import sys
import json
# DON\'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.product import Product, Article
from src.routes.user import user_bp
from src.routes.blog import blog_bp
from src.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), \'static\'))

# Enable CORS for all routes
CORS(app)

# Load configuration
app.config.from_object(Config)

# Register blueprints
app.register_blueprint(user_bp, url_prefix=\'/api\')
app.register_blueprint(blog_bp, url_prefix=\'/api/blog\')

# Import and register automation blueprint
from src.routes.automation import automation_bp
app.register_blueprint(automation_bp, url_prefix=\'/api/automation\')

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()
    logger.info("Database initialized successfully")

    if Config.USE_MOCK_DATA:
        from src.services.trend_analyzer import TrendAnalyzer
        from src.models.product import Product
        trend_analyzer = TrendAnalyzer(use_mock_data=True)
        mock_products = trend_analyzer._get_mock_trending_products(limit=10)
        for p_data in mock_products:
            # Check if product already exists to prevent duplicates
            existing_product = Product.query.filter_by(name=p_data["name"]).first()
            if not existing_product:
                product = Product(
                    name=p_data["name"],
                    description=p_data["description"],
                    category=p_data["category"],
                    price=p_data["price"],
                    currency=p_data["currency"],
                    trend_score=p_data["trend_score"],
                    search_volume=p_data["search_volume"],
                    competition_level=p_data["competition_level"],
                    affiliate_programs=json.dumps(p_data["affiliate_programs"]),
                    primary_keywords=json.dumps(p_data["primary_keywords"]),
                    secondary_keywords=json.dumps(p_data["secondary_keywords"]),
                    source_url=p_data["source_url"],
                    image_url=p_data["image_url"]
                )
                db.session.add(product)
        db.session.commit()
        logger.info("Mock products loaded into database.")

@app.route(\'/\', defaults={\'path\': \'\'}) 
@app.route(\'/<path:path>\')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, \'index.html\')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, \'index.html\')
        else:
            return "index.html not found", 404


if __name__ == \'__main__\':
    # Ensure database directory exists before running the app
    db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")
    app.run(host=\'0.0.0.0\', port=5000, debug=True)


