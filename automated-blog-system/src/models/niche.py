from datetime import datetime
from src.models.user import db
import json

class Niche(db.Model):
    """Niche model for organizing content by market segments."""
    
    __tablename__ = 'niches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    target_keywords = db.Column(db.Text)  # Comma-separated keywords
    target_audience = db.Column(db.Text)
    monetization_strategy = db.Column(db.Text)
    content_themes = db.Column(db.Text)  # Comma-separated themes
    affiliate_networks = db.Column(db.Text)  # Comma-separated networks
    competition_level = db.Column(db.String(20), default='medium')  # low, medium, high
    profitability_score = db.Column(db.Integer, default=0)  # 0-100
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='niche', lazy=True)
    articles = db.relationship('Article', backref='niche', lazy=True)
    
    def to_dict(self):
        """Convert niche to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_keywords': self.target_keywords.split(',') if self.target_keywords else [],
            'target_audience': self.target_audience,
            'monetization_strategy': self.monetization_strategy,
            'content_themes': self.content_themes.split(',') if self.content_themes else [],
            'affiliate_networks': self.affiliate_networks.split(',') if self.affiliate_networks else [],
            'competition_level': self.competition_level,
            'profitability_score': self.profitability_score,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'products_count': len(self.products) if self.products else 0,
            'articles_count': len(self.articles) if self.articles else 0
        }
    
    def __repr__(self):
        return f'<Niche {self.name}>'

