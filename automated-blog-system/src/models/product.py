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
    # PR #6.4 — affiliate link wiring
    affiliate_url = db.Column(db.String(500))   # raw affiliate destination URL
    tracking_id = db.Column(db.String(50))      # e.g. "deskcred-20" for Amazon Associates
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
            'affiliate_url': self.affiliate_url,
            'tracking_id': self.tracking_id,
            'niche_id': self.niche_id,
            'niche_name': self.niche.name if self.niche else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        
        return f'<Product {self.name} (ID: {self.id})  >'

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
    ghost_post_id = db.Column(db.String(64))
    published_url = db.Column(db.String(500))
    editorial_verdict = db.Column(db.String(20), default='PENDING')
    last_verdict_json = db.Column(db.Text)  # PR #2 — full EditorialVerdict; PR #3 mirrors to editorial_reports
    blueprint_id = db.Column(db.String(64))  # PR #2 stub; PR #5a backs this with a real Blueprint row
    current_stage = db.Column(db.String(40), default='stage_0')  # PR #2/#3 — flips on each transition
    stage_status = db.Column(db.String(20), default='pending')  # PR #3 — pending|running|complete|halted_budget|error
    cost_usd = db.Column(db.Numeric(10, 4), default=0)  # PR #3 — running per-article spend
    cost_budget_usd = db.Column(db.Numeric(10, 4), default=5)  # PR #3 — per-article cap (default $5.00)
    research_report_json = db.Column(db.Text)  # PR #3 — Stage 0 output
    strategy_json = db.Column(db.Text)  # PR #3 — Stage 1 output
    draft_sections_json = db.Column(db.Text)  # PR #3 — Stage 2 output
    monetization_map_json = db.Column(db.Text)  # PR #3 — Stage 2 output (CTA placement plan)
    last_error = db.Column(db.Text)  # PR #3 — last exception text
    last_transition_at = db.Column(db.DateTime)  # PR #3 — when current_stage was last set
    ghost_updated_at = db.Column(db.DateTime)  # PR #6 — Ghost-side updated_at for optimistic concurrency
    last_ghost_sync_hash = db.Column(db.String(128))  # PR #6 — sha256 of last (title+html+meta+tags) sent to / pulled from Ghost
    has_unpushed_changes = db.Column(db.Boolean, default=False, nullable=False)  # PR #6 — convenience flag derived from sync hash
    seo_score = db.Column(db.Float, default=0.0)
    readability_score = db.Column(db.Float, default=0.0)
    word_count = db.Column(db.Integer, default=0)
    affiliate_links_count = db.Column(db.Integer, default=0)
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
            'ghost_post_id': self.ghost_post_id,
            'published_url': self.published_url,
            'editorial_verdict': self.editorial_verdict,
            'last_verdict_json': self.last_verdict_json,
            'blueprint_id': self.blueprint_id,
            'current_stage': self.current_stage,
            'stage_status': self.stage_status,
            'cost_usd': str(self.cost_usd) if self.cost_usd is not None else "0",
            'cost_budget_usd': str(self.cost_budget_usd) if self.cost_budget_usd is not None else "0",
            'research_report_json': self.research_report_json,
            'strategy_json': self.strategy_json,
            'draft_sections_json': self.draft_sections_json,
            'monetization_map_json': self.monetization_map_json,
            'last_error': self.last_error,
            'last_transition_at': self.last_transition_at.isoformat() if self.last_transition_at else None,
            'ghost_updated_at': self.ghost_updated_at.isoformat() if self.ghost_updated_at else None,
            'last_ghost_sync_hash': self.last_ghost_sync_hash,
            'has_unpushed_changes': bool(self.has_unpushed_changes),
            'seo_score': self.seo_score,
            'readability_score': self.readability_score,
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_headless_contract(self):
        """Return the article in the Headless Article Contract shape consumed
        by GhostService.publish_article().

        PR #6.4 — calls_to_action is now populated from the linked Product's
        affiliate_url + tracking_id. If the product has no affiliate_url, no
        CTA is emitted (so the article still publishes, just without a link).
        """
        keywords = json.loads(self.keywords) if self.keywords else []

        ctas = []
        if self.product and self.product.affiliate_url:
            target = self.product.affiliate_url
            # If a tracking_id is set and the URL doesn't already contain it,
            # append it as a query param. We default to ?tag=<id> because
            # deskcred-20 is Amazon Associates format. A future PR will detect
            # the affiliate network properly (CJ, Impact, ShareASale use
            # different param names like 'subid' or 'sid').
            if self.product.tracking_id and "tag=" not in target:
                separator = "&" if "?" in target else "?"
                target = f"{target}{separator}tag={self.product.tracking_id}"
            ctas.append({
                "type": "affiliate",
                "target": target,
                "anchor": f"Check current price on {self.product.name}",
            })

        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "sections": [],
            "summary": (self.meta_description or "")[:300],
            "keywords": keywords,
            "calls_to_action": ctas,
            "meta": {
                "meta_title": self.title,
                "meta_description": self.meta_description,
            },
        }

    def __repr__(self):
        return f'<Article {self.title}>'
   
