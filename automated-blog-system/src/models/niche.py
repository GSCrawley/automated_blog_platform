from datetime import datetime
from src.models.user import db
import json

class Niche(db.Model):
    """Niche model for storing blog niche information."""
    
    __tablename__ = 'niches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    target_keywords = db.Column(db.Text)  # JSON string
    target_audience = db.Column(db.String(200))
    monetization_strategy = db.Column(db.Text)
    content_themes = db.Column(db.Text)  # JSON string
    affiliate_networks = db.Column(db.Text)  # JSON string
    competition_level = db.Column(db.String(20))  # low, medium, high
    profitability_score = db.Column(db.Float)
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
            'target_keywords': json.loads(self.target_keywords) if self.target_keywords else [],
            'target_audience': self.target_audience,
            'monetization_strategy': self.monetization_strategy,
            'content_themes': json.loads(self.content_themes) if self.content_themes else [],
            'affiliate_networks': json.loads(self.affiliate_networks) if self.affiliate_networks else [],
            'competition_level': self.competition_level,
            'profitability_score': self.profitability_score,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'products_count': len(self.products) if self.products else 0,
            'articles_count': len(self.articles) if self.articles else 0
        }

