from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.product import Product, Article
from src.services.trend_analyzer import TrendAnalyzer
from src.services.content_generator import ContentGenerator
from src.services.seo_optimizer import SEOOptimizer
import json

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/trending-products', methods=['GET'])
def get_trending_products():
    """Get trending products."""
    try:
        limit = request.args.get('limit', 10, type=int)
        trend_analyzer = TrendAnalyzer(use_mock_data=True)
        products = trend_analyzer.get_trending_products(limit=limit)
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products from database."""
    try:
        products = Product.query.all()
        return jsonify({
            'success': True, 
            'products': [product.to_dict() for product in products]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    try:
        data = request.get_json()
        product = Product(
            name=data['name'],
            description=data.get('description'),
            category=data.get('category'),
            price=data.get('price'),
            currency=data.get('currency', 'USD'),
            trend_score=data.get('trend_score'),
            search_volume=data.get('search_volume'),
            competition_level=data.get('competition_level'),
            affiliate_programs=json.dumps(data.get('affiliate_programs', [])),
            primary_keywords=json.dumps(data.get('primary_keywords', [])),
            secondary_keywords=json.dumps(data.get('secondary_keywords', [])),
            source_url=data.get('source_url'),
            image_url=data.get('image_url')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'product': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/articles', methods=['GET'])
def get_articles():
    """Get all articles from database."""
    try:
        articles = Article.query.all()
        return jsonify({
            'success': True, 
            'articles': [article.to_dict() for article in articles]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/generate-article', methods=['POST'])
def generate_article():
    """Generate a new article for a product."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'success': False, 'error': 'Product ID is required'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Generate content
        content_generator = ContentGenerator()
        article_data = content_generator.generate_article(product.to_dict())
        
        # Create article in database
        article = Article(
            title=article_data['title'],
            content=article_data['content'],
            meta_description=article_data['meta_description'],
            keywords=json.dumps(article_data['keywords']),
            product_id=product_id,
            seo_score=article_data.get('seo_score'),
            readability_score=article_data.get('readability_score'),
            word_count=len(article_data['content'].split()),
            affiliate_links_count=article_data.get('affiliate_links_count', 0)
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({'success': True, 'article': article.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/keyword-research', methods=['POST'])
def keyword_research():
    """Perform keyword research for a topic."""
    try:
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'}), 400
        
        seo_optimizer = SEOOptimizer()
        keywords = seo_optimizer.research_keywords(topic)
        
        return jsonify({'success': True, 'keywords': keywords})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

