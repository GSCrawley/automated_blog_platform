from flask import Blueprint, request, jsonify
from src.models.product import db, Product, Article
from src.services.trend_analyzer import TrendAnalyzer
from src.services.content_generator import ContentGenerator
from src.services.seo_optimizer import SEOOptimizer
from src.config import Config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

blog_bp = Blueprint('blog', __name__)

# Initialize services
trend_analyzer = TrendAnalyzer(use_mock_data=Config.USE_MOCK_DATA)
content_generator = ContentGenerator()
seo_optimizer = SEOOptimizer()

@blog_bp.route('/trending-products', methods=['GET'])
def get_trending_products():
    """Get trending high-ticket products."""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 10))
        
        products = trend_analyzer.get_trending_products(category=category, limit=limit)
        
        return jsonify({
            'success': True,
            'data': products,
            'count': len(products)
        })
    
    except Exception as e:
        logger.error(f"Error getting trending products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product in the database."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create new product
        product = Product(
            name=data['name'],
            description=data.get('description'),
            category=data['category'],
            price=data['price'],
            currency=data.get('currency', 'USD'),
            trend_score=data.get('trend_score', 0.0),
            search_volume=data.get('search_volume', 0),
            competition_level=data.get('competition_level'),
            commission_rate=data.get('commission_rate'),
            commission_type=data.get('commission_type'),
            source_url=data.get('source_url'),
            image_url=data.get('image_url')
        )
        
        # Set JSON fields
        if 'affiliate_programs' in data:
            product.set_affiliate_programs(data['affiliate_programs'])
        
        if 'primary_keywords' in data:
            product.set_primary_keywords(data['primary_keywords'])
        
        if 'secondary_keywords' in data:
            product.set_secondary_keywords(data['secondary_keywords'])
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products from the database."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        category = request.args.get('category')
        
        query = Product.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        products = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': products.total,
                'pages': products.pages
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID."""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/keyword-research', methods=['POST'])
def research_keywords():
    """Research keywords for a given topic."""
    try:
        data = request.get_json()
        topic = data.get('topic')
        num_keywords = data.get('num_keywords', 20)
        
        if not topic:
            return jsonify({
                'success': False,
                'error': 'Topic is required'
            }), 400
        
        keywords = seo_optimizer.research_keywords(topic, num_keywords)
        
        return jsonify({
            'success': True,
            'data': keywords
        })
    
    except Exception as e:
        logger.error(f"Error researching keywords: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/generate-article', methods=['POST'])
def generate_article():
    """Generate an article for a product."""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        target_keywords = data.get('target_keywords', [])
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Product ID is required'
            }), 400
        
        # Get product from database
        product = Product.query.get_or_404(product_id)
        product_data = product.to_dict()
        
        # Generate article
        article_data = content_generator.generate_article(product_data, target_keywords)
        
        # Create article in database
        article = Article(
            title=article_data['title'],
            slug=article_data['slug'],
            content=article_data['content'],
            excerpt=article_data['excerpt'],
            meta_title=article_data['meta_title'],
            meta_description=article_data['meta_description'],
            focus_keyword=article_data['focus_keyword'],
            product_id=product_id
        )
        
        article.set_keywords(article_data['keywords'])
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'article': article.to_dict(),
                'generation_stats': {
                    'word_count': article_data['word_count'],
                    'readability_score': article_data['readability_score'],
                    'affiliate_links_count': article_data['affiliate_links_count']
                }
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Error generating article: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/articles', methods=['GET'])
def get_articles():
    """Get all articles."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status')
        
        query = Article.query
        
        if status:
            query = query.filter_by(status=status)
        
        articles = query.order_by(Article.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [article.to_dict() for article in articles.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': articles.total,
                'pages': articles.pages
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/articles/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """Get a specific article by ID."""
    try:
        article = Article.query.get_or_404(article_id)
        return jsonify({
            'success': True,
            'data': article.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """Update an article."""
    try:
        article = Article.query.get_or_404(article_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            article.title = data['title']
        if 'content' in data:
            article.content = data['content']
        if 'excerpt' in data:
            article.excerpt = data['excerpt']
        if 'meta_title' in data:
            article.meta_title = data['meta_title']
        if 'meta_description' in data:
            article.meta_description = data['meta_description']
        if 'focus_keyword' in data:
            article.focus_keyword = data['focus_keyword']
        if 'status' in data:
            article.status = data['status']
        if 'keywords' in data:
            article.set_keywords(data['keywords'])
        
        article.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': article.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error updating article: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/optimize-content', methods=['POST'])
def optimize_content():
    """Optimize content for SEO."""
    try:
        data = request.get_json()
        content = data.get('content')
        target_keyword = data.get('target_keyword')
        
        if not content or not target_keyword:
            return jsonify({
                'success': False,
                'error': 'Content and target keyword are required'
            }), 400
        
        optimization = seo_optimizer.optimize_content(content, target_keyword)
        
        return jsonify({
            'success': True,
            'data': optimization
        })
    
    except Exception as e:
        logger.error(f"Error optimizing content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/analyze-competition', methods=['POST'])
def analyze_competition():
    """Analyze competition for a keyword."""
    try:
        data = request.get_json()
        keyword = data.get('keyword')
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': 'Keyword is required'
            }), 400
        
        analysis = seo_optimizer.analyze_competition(keyword)
        
        return jsonify({
            'success': True,
            'data': analysis
        })
    
    except Exception as e:
        logger.error(f"Error analyzing competition: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blog_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get basic counts
        total_products = Product.query.filter_by(is_active=True).count()
        total_articles = Article.query.count()
        published_articles = Article.query.filter_by(status='published').count()
        draft_articles = Article.query.filter_by(status='draft').count()
        
        # Get recent articles
        recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
        
        # Get top performing articles (mock data for now)
        top_articles = Article.query.order_by(Article.views.desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'data': {
                'totals': {
                    'products': total_products,
                    'articles': total_articles,
                    'published_articles': published_articles,
                    'draft_articles': draft_articles
                },
                'recent_articles': [article.to_dict() for article in recent_articles],
                'top_articles': [article.to_dict() for article in top_articles]
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
