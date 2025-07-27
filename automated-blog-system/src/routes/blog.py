from flask import Blueprint, request, jsonify
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/trending-products', methods=['GET'])
def get_trending_products():
    """Get trending products from various sources."""
    try:
        from src.services.trend_analyzer import TrendAnalyzer
        from src.config import Config
        
        trend_analyzer = TrendAnalyzer(use_mock_data=Config.USE_MOCK_DATA)
        products = trend_analyzer.get_trending_products()
        
        return jsonify({
            'success': True,
            'products': products
        })
    except Exception as e:
        logger.error(f"Error fetching trending products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products."""
    try:
        from src.models.product import Product
        
        niche_id = request.args.get('niche_id')
        if niche_id:
            products = Product.query.filter_by(niche_id=niche_id).all()
        else:
            products = Product.query.all()
        
        return jsonify({
            'success': True,
            'products': [product.to_dict() for product in products]
        })
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    try:
        from src.models.product import Product
        from src.models.user import db
        
        data = request.get_json()
        
        product = Product(
            name=data.get('name'),
            description=data.get('description'),
            category=data.get('category'),
            price=data.get('price'),
            currency=data.get('currency', 'USD'),
            trend_score=data.get('trend_score', 0),
            search_volume=data.get('search_volume', 0),
            competition_level=data.get('competition_level', 'medium'),
            affiliate_programs=json.dumps(data.get('affiliate_programs', [])),
            primary_keywords=json.dumps(data.get('primary_keywords', [])),
            secondary_keywords=json.dumps(data.get('secondary_keywords', [])),
            source_url=data.get('source_url'),
            image_url=data.get('image_url'),
            niche_id=data.get('niche_id')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product."""
    try:
        from src.models.product import Product
        
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/keyword-research', methods=['POST'])
def keyword_research():
    """Perform keyword research for a given topic."""
    try:
        from src.services.seo_optimizer import SEOOptimizer
        
        data = request.get_json()
        topic = data.get('topic')
        niche_id = data.get('niche_id')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'}), 400
        
        seo_optimizer = SEOOptimizer()
        keywords = seo_optimizer.research_keywords(topic, niche_id=niche_id)
        
        return jsonify({
            'success': True,
            'keywords': keywords
        })
    except Exception as e:
        logger.error(f"Error performing keyword research: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/generate-article', methods=['POST'])
def generate_article():
    """Generate an article for a product."""
    try:
        from src.services.content_generator import ContentGenerator
        from src.models.product import Product
        
        data = request.get_json()
        product_id = data.get('product_id')
        niche_id = data.get('niche_id')
        
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID is required'}), 400
        
        product = Product.query.get_or_404(product_id)
        content_generator = ContentGenerator()
        
        article_data = content_generator.generate_article(product, niche_id=niche_id)
        
        return jsonify({
            'success': True,
            'article': article_data
        })
    except Exception as e:
        logger.error(f"Error generating article: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/articles', methods=['GET'])
def get_articles():
    """Get all articles."""
    try:
        from src.models.product import Article
        
        niche_id = request.args.get('niche_id')
        if niche_id:
            articles = Article.query.filter_by(niche_id=niche_id).all()
        else:
            articles = Article.query.all()
        
        return jsonify({
            'success': True,
            'articles': [article.to_dict() for article in articles]
        })
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get a specific article."""
    try:
        from src.models.product import Article
        
        article = Article.query.get_or_404(article_id)
        return jsonify({
            'success': True,
            'article': article.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching article: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """Update an article."""
    try:
        from src.models.product import Article
        from src.models.user import db
        
        article = Article.query.get_or_404(article_id)
        data = request.get_json()
        
        # Update article fields
        for field in ['title', 'content', 'meta_description', 'keywords', 'status']:
            if field in data:
                if field == 'keywords':
                    setattr(article, field, json.dumps(data[field]))
                else:
                    setattr(article, field, data[field])
        
        article.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'article': article.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/optimize-content', methods=['POST'])
def optimize_content():
    """Optimize content for SEO."""
    try:
        from src.services.seo_optimizer import SEOOptimizer
        
        data = request.get_json()
        content = data.get('content')
        target_keywords = data.get('target_keywords', [])
        niche_id = data.get('niche_id')
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        seo_optimizer = SEOOptimizer()
        optimized_content = seo_optimizer.optimize_content(content, target_keywords, niche_id=niche_id)
        
        return jsonify({
            'success': True,
            'optimized_content': optimized_content
        })
    except Exception as e:
        logger.error(f"Error optimizing content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/analyze-competition', methods=['POST'])
def analyze_competition():
    """Analyze competition for given keywords."""
    try:
        from src.services.seo_optimizer import SEOOptimizer
        
        data = request.get_json()
        keywords = data.get('keywords', [])
        niche_id = data.get('niche_id')
        
        if not keywords:
            return jsonify({'success': False, 'error': 'Keywords are required'}), 400
        
        seo_optimizer = SEOOptimizer()
        analysis = seo_optimizer.analyze_competition(keywords, niche_id=niche_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error analyzing competition: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        from src.models.product import Product, Article
        from src.models.niche import Niche
        
        niche_id = request.args.get('niche_id')
        
        if niche_id:
            products_count = Product.query.filter_by(niche_id=niche_id).count()
            articles_count = Article.query.filter_by(niche_id=niche_id).count()
        else:
            products_count = Product.query.count()
            articles_count = Article.query.count()
        
        niches_count = Niche.query.filter_by(active=True).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'products': products_count,
                'articles': articles_count,
                'niches': niches_count,
                'active_campaigns': 0  # Placeholder
            }
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Niche management routes
@blog_bp.route('/niches', methods=['GET'])
def get_niches():
    """Get all active niches."""
    try:
        from src.models.niche import Niche
        niches = Niche.query.filter_by(active=True).all()
        return jsonify({
            'success': True,
            'niches': [niche.to_dict() for niche in niches]
        })
    except Exception as e:
        logger.error(f"Error fetching niches: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/niches', methods=['POST'])
def create_niche():
    """Create a new niche."""
    try:
        from src.models.niche import Niche
        from src.models.user import db
        
        data = request.get_json()
        
        # Check if niche with same name exists
        existing_niche = Niche.query.filter_by(name=data.get('name')).first()
        if existing_niche:
            return jsonify({
                'success': False,
                'error': 'Niche with this name already exists'
            }), 400
        
        # Create new niche
        niche = Niche(
            name=data.get('name'),
            description=data.get('description', ''),
            target_keywords=data.get('target_keywords', ''),
            target_audience=data.get('target_audience', ''),
            monetization_strategy=data.get('monetization_strategy', ''),
            content_themes=data.get('content_themes', ''),
            affiliate_networks=data.get('affiliate_networks', ''),
            competition_level=data.get('competition_level', 'medium'),
            profitability_score=data.get('profitability_score', 0)
        )
        
        db.session.add(niche)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'niche': niche.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error creating niche: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/niches/<int:niche_id>', methods=['GET'])
def get_niche(niche_id):
    """Get a specific niche."""
    try:
        from src.models.niche import Niche
        niche = Niche.query.get_or_404(niche_id)
        return jsonify({
            'success': True,
            'niche': niche.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching niche: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/niches/<int:niche_id>', methods=['PUT'])
def update_niche(niche_id):
    """Update a niche."""
    try:
        from src.models.niche import Niche
        from src.models.user import db
        
        niche = Niche.query.get_or_404(niche_id)
        data = request.get_json()
        
        # Update niche fields
        for field in ['name', 'description', 'target_keywords', 'target_audience', 
                     'monetization_strategy', 'content_themes', 'affiliate_networks', 
                     'competition_level', 'profitability_score']:
            if field in data:
                setattr(niche, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'niche': niche.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating niche: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/niches/<int:niche_id>', methods=['DELETE'])
def delete_niche(niche_id):
    """Delete a niche (soft delete by setting active=False)."""
    try:
        from src.models.niche import Niche
        from src.models.user import db
        
        niche = Niche.query.get_or_404(niche_id)
        niche.active = False
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting niche: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

