from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.product import Product, Article
from src.models.user import db
from src.services.trend_analyzer import TrendAnalyzer
from src.services.content_generator import ContentGenerator
from src.services.seo_optimizer import SEOOptimizer
from src.services.wordpress_service import WordPressService
from src.config import Config
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Post article to WordPress if configuration is available
        if all([Config.WORDPRESS_API_URL, Config.WORDPRESS_USERNAME, Config.WORDPRESS_PASSWORD]):
            try:
                logger.info(f"Posting article '{article.title}' to WordPress")
                wordpress_service = WordPressService()
                wp_response = wordpress_service.post_article(article)
                
                if wp_response['success']:
                    # Update article with WordPress post ID
                    article.wordpress_post_id = wp_response['wordpress_post_id']
                    article.status = 'published'
                    article.published_at = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"Article posted to WordPress successfully with ID: {wp_response['wordpress_post_id']}")
                    logger.info(f"WordPress URL: {wp_response.get('wordpress_url')}")
                else:
                    logger.error(f"Failed to post article to WordPress: {wp_response.get('error')}")
            except Exception as wp_error:
                logger.error(f"Error during WordPress integration: {str(wp_error)}")
        else:
            logger.warning("WordPress integration skipped: Missing configuration")
        
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
    except Exception as e:  # Add this except block
        return jsonify({'success': False, 'error': str(e)}), 500          
    
@blog_bp.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """Update an article."""
    try:
        data = request.get_json()
        article = Article.query.get_or_404(article_id)
        
        # Update fields if provided
        if 'status' in data:
            article.status = data['status']
        if 'title' in data:
            article.title = data['title']
        if 'content' in data:
            article.content = data['content']
        if 'meta_description' in data:
            article.meta_description = data['meta_description']
        
        article.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update on WordPress if it was posted there
        if article.wordpress_post_id:
            try:
                logger.info(f"Updating article on WordPress (ID: {article.wordpress_post_id})")
                wordpress_service = WordPressService()
                wp_response = wordpress_service.update_article(article)
                
                if wp_response['success']:
                    logger.info("Article updated on WordPress successfully")
                else:
                    logger.warning(f"Failed to update article on WordPress: {wp_response.get('error')}")
            except Exception as wp_error:
                logger.error(f"Error during WordPress update: {str(wp_error)}")
        
        return jsonify({
            'success': True,
            'message': 'Article updated successfully',
            'article': article.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """Delete an article."""
    try:
        article = Article.query.get_or_404(article_id)
        
        # Delete from WordPress if it was posted there
        if article.wordpress_post_id:
            try:
                logger.info(f"Deleting article from WordPress (ID: {article.wordpress_post_id})")
                wordpress_service = WordPressService()
                wp_response = wordpress_service.delete_article(article.wordpress_post_id)
                
                if wp_response['success']:
                    logger.info("Article deleted from WordPress successfully")
                else:
                    logger.warning(f"Failed to delete article from WordPress: {wp_response.get('error')}")
            except Exception as wp_error:
                logger.error(f"Error during WordPress deletion: {str(wp_error)}")
        
        # Delete from database
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Article deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product."""
    try:
        data = request.get_json()
        product = Product.query.get_or_404(product_id)
        
        # Update fields if provided
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'category' in data:
            product.category = data['category']
        if 'price' in data:
            product.price = data['price']
        if 'trend_score' in data:
            product.trend_score = data['trend_score']
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'product': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product."""
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/wordpress/categories', methods=['GET'])
def get_wordpress_categories():
    """Get WordPress categories."""
    try:
        if all([Config.WORDPRESS_API_URL, Config.WORDPRESS_USERNAME, Config.WORDPRESS_PASSWORD]):
            wordpress_service = WordPressService()
            categories = wordpress_service.get_categories()
            return jsonify({'success': True, 'categories': categories})
        else:
            return jsonify({'success': False, 'error': 'WordPress configuration is incomplete'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/wordpress/tags', methods=['GET'])
def get_wordpress_tags():
    """Get WordPress tags."""
    try:
        if all([Config.WORDPRESS_API_URL, Config.WORDPRESS_USERNAME, Config.WORDPRESS_PASSWORD]):
            wordpress_service = WordPressService()
            tags = wordpress_service.get_tags()
            return jsonify({'success': True, 'tags': tags})
        else:
            return jsonify({'success': False, 'error': 'WordPress configuration is incomplete'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/wordpress/settings', methods=['GET'])
def get_wordpress_settings():
    """Get WordPress settings."""
    try:
        if all([Config.WORDPRESS_API_URL, Config.WORDPRESS_USERNAME, Config.WORDPRESS_PASSWORD]):
            wordpress_service = WordPressService()
            settings = wordpress_service.get_settings()
            return jsonify({'success': True, 'settings': settings})
        else:
            return jsonify({'success': False, 'error': 'WordPress configuration is incomplete'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@blog_bp.route('/articles/<int:article_id>/wordpress-status', methods=['GET'])
def get_article_wordpress_status(article_id):
    """Get WordPress status for an article."""
    try:
        article = Article.query.get_or_404(article_id)
        
        if not article.wordpress_post_id:
            return jsonify({
                'success': True,
                'status': 'not_published',
                'message': 'Article not published to WordPress'
            })
        
        # Get status from WordPress
        try:
            wordpress_service = WordPressService()
            wp_response = wordpress_service.get_article(article.wordpress_post_id)
            
            if wp_response['success']:
                wp_article = wp_response['article']
                return jsonify({
                    'success': True,
                    'status': wp_article.get('status', 'unknown'),
                    'url': wp_article.get('link'),
                    'modified': wp_article.get('modified'),
                    'wordpress_id': article.wordpress_post_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': wp_response.get('error', 'Failed to get WordPress status')
                }), 400
                
        except Exception as wp_error:
            logger.error(f"Error getting WordPress status: {str(wp_error)}")
            return jsonify({
                'success': False,
                'error': str(wp_error)
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500