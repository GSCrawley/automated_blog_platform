from datetime import datetime
from src.models.user import db
import json

class Product(db.Model):
    """Product model for storing affiliate products."""
    
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    price = db.Column(db.Float)
    currency = db.Column(db.String(10), default='USD')
    trend_score = db.Column(db.Float, default=0.0)
    search_volume = db.Column(db.Integer, default=0)
    competition_level = db.Column(db.String(20), default='medium')
    affiliate_programs = db.Column(db.Text)  # JSON string
    primary_keywords = db.Column(db.Text)  # JSON string
    secondary_keywords = db.Column(db.Text)  # JSON string
    source_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    niche_id = db.Column(db.Integer, db.ForeignKey('niches.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
            'primary_keywords': json.loads(self.primary_keywords) if self.primary_keywords else [],
            'secondary_keywords': json.loads(self.secondary_keywords) if self.secondary_keywords else [],
            'source_url': self.source_url,
            'image_url': self.image_url,
            'niche_id': self.niche_id,
            'niche_name': self.niche.name if self.niche else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Article(db.Model):
    """Article model for storing generated content."""
    
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    meta_description = db.Column(db.String(160))
    keywords = db.Column(db.Text)  # JSON string
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    niche_id = db.Column(db.Integer, db.ForeignKey('niches.id'), nullable=True)
    wordpress_post_id = db.Column(db.Integer)
    seo_score = db.Column(db.Float, default=0.0)
    readability_score = db.Column(db.Float, default=0.0)
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='articles')
    
    def to_dict(self):
        """Convert article to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'meta_description': self.meta_description,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'status': self.status,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'niche_id': self.niche_id,
            'niche_name': self.niche.name if self.niche else None,
            'wordpress_post_id': self.wordpress_post_id,
            'seo_score': self.seo_score,
            'readability_score': self.readability_score,
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Article {self.title}>'

