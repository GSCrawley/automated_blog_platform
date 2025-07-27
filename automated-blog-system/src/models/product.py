from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    """Model for trending high-ticket products."""
    
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='USD')
    
    # Trending data
    trend_score = db.Column(db.Float, default=0.0)
    search_volume = db.Column(db.Integer, default=0)
    competition_level = db.Column(db.String(20))  # low, medium, high
    
    # Affiliate data
    affiliate_programs = db.Column(db.Text)  # JSON string of affiliate programs
    commission_rate = db.Column(db.Float)
    commission_type = db.Column(db.String(20))  # percentage, fixed
    
    # SEO data
    primary_keywords = db.Column(db.Text)  # JSON string of keywords
    secondary_keywords = db.Column(db.Text)  # JSON string of keywords
    
    # Metadata
    source_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        """Convert product to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'currency': self.currency,
            'trend_score': self.trend_score,
            'search_volume': self.search_volume,
            'competition_level': self.competition_level,
            'affiliate_programs': json.loads(self.affiliate_programs) if self.affiliate_programs else [],
            'commission_rate': self.commission_rate,
            'commission_type': self.commission_type,
            'primary_keywords': json.loads(self.primary_keywords) if self.primary_keywords else [],
            'secondary_keywords': json.loads(self.secondary_keywords) if self.secondary_keywords else [],
            'source_url': self.source_url,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_affiliate_programs(self, programs):
        """Set affiliate programs as JSON string."""
        self.affiliate_programs = json.dumps(programs)
    
    def get_affiliate_programs(self):
        """Get affiliate programs as list."""
        return json.loads(self.affiliate_programs) if self.affiliate_programs else []
    
    def set_primary_keywords(self, keywords):
        """Set primary keywords as JSON string."""
        self.primary_keywords = json.dumps(keywords)
    
    def get_primary_keywords(self):
        """Get primary keywords as list."""
        return json.loads(self.primary_keywords) if self.primary_keywords else []
    
    def set_secondary_keywords(self, keywords):
        """Set secondary keywords as JSON string."""
        self.secondary_keywords = json.dumps(keywords)
    
    def get_secondary_keywords(self):
        """Get secondary keywords as list."""
        return json.loads(self.secondary_keywords) if self.secondary_keywords else []


class Article(db.Model):
    """Model for generated blog articles."""
    
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    
    # SEO data
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    focus_keyword = db.Column(db.String(100))
    keywords = db.Column(db.Text)  # JSON string of keywords
    
    # Product relationship
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('articles', lazy=True))
    
    # Publishing data
    status = db.Column(db.String(20), default='draft')  # draft, published, scheduled
    wordpress_post_id = db.Column(db.Integer)
    published_at = db.Column(db.DateTime)
    
    # Performance data
    views = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Article {self.title}>'
    
    def to_dict(self):
        """Convert article to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'focus_keyword': self.focus_keyword,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'product_id': self.product_id,
            'status': self.status,
            'wordpress_post_id': self.wordpress_post_id,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'views': self.views,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'revenue': self.revenue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def set_keywords(self, keywords):
        """Set keywords as JSON string."""
        self.keywords = json.dumps(keywords)
    
    def get_keywords(self):
        """Get keywords as list."""
        return json.loads(self.keywords) if self.keywords else []

