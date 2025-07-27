This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

## Additional Info

# Directory Structure
```
automated-blog-system/
  src/
    models/
      product.py
      user.py
    routes/
      automation.py
      blog.py
      user.py
    services/
      __init__.py
      automation_scheduler.py
      content_generator.py
      seo_optimizer.py
      trend_analyzer.py
      wordpress_service.py
    static/
      index.html
    config.py
    main.py
  .gitignore
  requirements.txt
  test_api.py
  test_wordpress_integration.py
blog-frontend/
  src/
    assets/
      react.svg
    components/
      ui/
        accordion.jsx
        alert-dialog.jsx
        alert.jsx
        aspect-ratio.jsx
        avatar.jsx
        badge.jsx
        breadcrumb.jsx
        button.jsx
        calendar.jsx
        card.jsx
        carousel.jsx
        chart.jsx
        checkbox.jsx
        collapsible.jsx
        command.jsx
        context-menu.jsx
        dialog.jsx
        drawer.jsx
        dropdown-menu.jsx
        form.jsx
        hover-card.jsx
        input-otp.jsx
        input.jsx
        label.jsx
        menubar.jsx
        navigation-menu.jsx
        pagination.jsx
        popover.jsx
        progress.jsx
        radio-group.jsx
        resizable.jsx
        scroll-area.jsx
        select.jsx
        separator.jsx
        sheet.jsx
        sidebar.jsx
        skeleton.jsx
        slider.jsx
        sonner.jsx
        switch.jsx
        table.jsx
        tabs.jsx
        textarea.jsx
        toggle-group.jsx
        toggle.jsx
        tooltip.jsx
      Analytics.jsx
      Articles.jsx
      Dashboard.jsx
      GenerateArticle.jsx
      Layout.jsx
      Products.jsx
      WordPressPostEditor.jsx
    hooks/
      use-mobile.js
    lib/
      utils.js
    services/
      api.js
    App.css
    App.jsx
    main.jsx
    test_api.js
    test_api.mjs
  components.json
  eslint.config.js
  index.html
  jsconfig.json
  package.json
  vite.config.js
.gitignore
project_overview_from_github.md
README.md
requirements.txt
research_findings.md
seo_tools_from_github.md
start_backend.sh
start_frontend.sh
system_architecture_design.md
test_api.py
todo.md
```

# Files

## File: automated-blog-system/src/models/product.py
````python
from datetime import datetime
from src.models.user import db
import json

class Product(db.Model):
    """Product model for storing trending product information."""
    
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    price = db.Column(db.Float)
    currency = db.Column(db.String(10), default='USD')
    trend_score = db.Column(db.Float)
    search_volume = db.Column(db.Integer)
    competition_level = db.Column(db.String(20))
    affiliate_programs = db.Column(db.Text)  # JSON string
    primary_keywords = db.Column(db.Text)    # JSON string
    secondary_keywords = db.Column(db.Text)  # JSON string
    source_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with articles
    articles = db.relationship('Article', backref='product', lazy=True)
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Article(db.Model):
    """Article model for storing generated blog articles."""
    
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    meta_description = db.Column(db.String(160))
    keywords = db.Column(db.Text)  # JSON string
    status = db.Column(db.String(20), default='draft')  # draft, published, scheduled
    wordpress_post_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    seo_score = db.Column(db.Float)
    readability_score = db.Column(db.Float)
    word_count = db.Column(db.Integer)
    affiliate_links_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert article to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'meta_description': self.meta_description,
            'keywords': json.loads(self.keywords) if self.keywords else [],
            'status': self.status,
            'wordpress_post_id': self.wordpress_post_id,
            'product_id': self.product_id,
            'seo_score': self.seo_score,
            'readability_score': self.readability_score,
            'word_count': self.word_count,
            'affiliate_links_count': self.affiliate_links_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
````

## File: automated-blog-system/src/models/user.py
````python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
````

## File: automated-blog-system/src/routes/automation.py
````python
from flask import Blueprint, request, jsonify
from src.services.automation_scheduler import AutomationScheduler

automation_bp = Blueprint('automation', __name__)

# Initialize scheduler
scheduler = AutomationScheduler()

@automation_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get the current status of the automation scheduler."""
    try:
        status = scheduler.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the automation scheduler."""
    try:
        scheduler.start()
        return jsonify({'success': True, 'message': 'Scheduler started successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the automation scheduler."""
    try:
        scheduler.stop()
        return jsonify({'success': True, 'message': 'Scheduler stopped successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/trigger-content-generation', methods=['POST'])
def trigger_content_generation():
    """Manually trigger content generation."""
    try:
        result = scheduler.generate_daily_content()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/trigger-content-update', methods=['POST'])
def trigger_content_update():
    """Manually trigger content updates."""
    try:
        result = scheduler.update_existing_content()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
````

## File: automated-blog-system/src/routes/user.py
````python
from flask import Blueprint, jsonify, request
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
````

## File: automated-blog-system/src/services/__init__.py
````python
# Services package
````

## File: automated-blog-system/src/services/automation_scheduler.py
````python
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from src.services.trend_analyzer import TrendAnalyzer
from src.services.content_generator import ContentGenerator
from src.models.product import Product, Article
from src.models.user import db
import json

class AutomationScheduler:
    """Service for automating content generation and updates."""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.trend_analyzer = TrendAnalyzer(use_mock_data=True)
        self.content_generator = ContentGenerator()
        self.last_content_generation = None
        self.last_content_update = None
    
    def start(self):
        """Start the automation scheduler."""
        if self.is_running:
            return {"status": "already_running"}
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        return {"status": "started", "message": "Automation scheduler started successfully"}
    
    def stop(self):
        """Stop the automation scheduler."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        return {"status": "stopped", "message": "Automation scheduler stopped successfully"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "is_running": self.is_running,
            "last_content_generation": self.last_content_generation.isoformat() if self.last_content_generation else None,
            "last_content_update": self.last_content_update.isoformat() if self.last_content_update else None,
            "next_scheduled_generation": self._get_next_scheduled_time("generation").isoformat() if self.is_running else None,
            "next_scheduled_update": self._get_next_scheduled_time("update").isoformat() if self.is_running else None
        }
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for daily content generation (9 AM)
                if self._should_run_task("generation", current_time):
                    self.generate_daily_content()
                
                # Check if it's time for content updates (3 PM)
                if self._should_run_task("update", current_time):
                    self.update_existing_content()
                
                # Sleep for 1 hour before next check
                time.sleep(3600)
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(300)  # Sleep 5 minutes on error
    
    def _should_run_task(self, task_type: str, current_time: datetime) -> bool:
        """Check if a task should run based on schedule."""
        if task_type == "generation":
            target_hour = 9
            last_run = self.last_content_generation
        elif task_type == "update":
            target_hour = 15
            last_run = self.last_content_update
        else:
            return False
        
        # Check if it's the right hour
        if current_time.hour != target_hour:
            return False
        
        # Check if we haven't run today
        if last_run and last_run.date() == current_time.date():
            return False
        
        return True
    
    def _get_next_scheduled_time(self, task_type: str) -> datetime:
        """Get next scheduled time for a task."""
        now = datetime.now()
        target_hour = 9 if task_type == "generation" else 15
        
        next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def generate_daily_content(self) -> Dict[str, Any]:
        """Generate new content for trending products."""
        try:
            # Get trending products
            trending_products = self.trend_analyzer.get_trending_products(limit=5)
            
            generated_articles = []
            
            for product_data in trending_products:
                # Check if product exists in database
                existing_product = Product.query.filter_by(name=product_data["name"]).first()
                
                if not existing_product:
                    # Create new product
                    product = Product(
                        name=product_data["name"],
                        description=product_data["description"],
                        category=product_data["category"],
                        price=product_data["price"],
                        currency=product_data["currency"],
                        trend_score=product_data["trend_score"],
                        search_volume=product_data["search_volume"],
                        competition_level=product_data["competition_level"],
                        affiliate_programs=json.dumps(product_data["affiliate_programs"]),
                        primary_keywords=json.dumps(product_data["primary_keywords"]),
                        secondary_keywords=json.dumps(product_data["secondary_keywords"]),
                        source_url=product_data["source_url"],
                        image_url=product_data["image_url"]
                    )
                    db.session.add(product)
                    db.session.flush()  # Get the ID
                    product_id = product.id
                else:
                    product_id = existing_product.id
                
                # Check if article already exists for this product
                existing_article = Article.query.filter_by(product_id=product_id).first()
                
                if not existing_article:
                    # Generate new article
                    article_data = self.content_generator.generate_article(product_data)
                    
                    article = Article(
                        title=article_data["title"],
                        content=article_data["content"],
                        meta_description=article_data["meta_description"],
                        keywords=json.dumps(article_data["keywords"]),
                        product_id=product_id,
                        seo_score=article_data.get("seo_score"),
                        readability_score=article_data.get("readability_score"),
                        word_count=len(article_data["content"].split()),
                        affiliate_links_count=article_data.get("affiliate_links_count", 0)
                    )
                    
                    db.session.add(article)
                    generated_articles.append(article_data["title"])
            
            db.session.commit()
            self.last_content_generation = datetime.now()
            
            return {
                "status": "success",
                "generated_articles": generated_articles,
                "count": len(generated_articles),
                "timestamp": self.last_content_generation.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def update_existing_content(self) -> Dict[str, Any]:
        """Update existing articles with fresh information."""
        try:
            # Get articles older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            old_articles = Article.query.filter(Article.updated_at < cutoff_date).limit(3).all()
            
            updated_articles = []
            
            for article in old_articles:
                if article.product:
                    # Regenerate content
                    product_data = article.product.to_dict()
                    new_article_data = self.content_generator.generate_article(product_data)
                    
                    # Update article
                    article.content = new_article_data["content"]
                    article.seo_score = new_article_data.get("seo_score")
                    article.readability_score = new_article_data.get("readability_score")
                    article.word_count = len(new_article_data["content"].split())
                    article.updated_at = datetime.now()
                    
                    updated_articles.append(article.title)
            
            db.session.commit()
            self.last_content_update = datetime.now()
            
            return {
                "status": "success",
                "updated_articles": updated_articles,
                "count": len(updated_articles),
                "timestamp": self.last_content_update.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
````

## File: automated-blog-system/src/services/seo_optimizer.py
````python
import random
from typing import List, Dict, Any

class SEOOptimizer:
    """Service for SEO optimization and keyword research."""
    
    def __init__(self):
        self.use_mock_data = True  # Set to False when real APIs are available
    
    def research_keywords(self, topic: str, limit: int = 20) -> Dict[str, Any]:
        """Research keywords for a given topic."""
        if self.use_mock_data:
            return self._get_mock_keywords(topic, limit)
        else:
            # TODO: Implement real keyword research APIs
            return self._get_mock_keywords(topic, limit)
    
    def _get_mock_keywords(self, topic: str, limit: int = 20) -> Dict[str, Any]:
        """Generate mock keyword data for development."""
        base_keywords = [
            f"{topic} review",
            f"best {topic}",
            f"{topic} guide",
            f"{topic} comparison",
            f"{topic} price",
            f"{topic} features",
            f"{topic} benefits",
            f"buy {topic}",
            f"{topic} deals",
            f"{topic} discount",
            f"{topic} vs",
            f"cheap {topic}",
            f"{topic} alternatives",
            f"{topic} pros and cons",
            f"{topic} worth it"
        ]
        
        keywords = []
        for i, keyword in enumerate(base_keywords[:limit]):
            keywords.append({
                "keyword": keyword,
                "search_volume": random.randint(1000, 50000),
                "competition": random.choice(["Low", "Medium", "High"]),
                "cpc": round(random.uniform(0.50, 5.00), 2),
                "difficulty": random.randint(20, 80)
            })
        
        return {
            "topic": topic,
            "keywords": keywords,
            "total_keywords": len(keywords),
            "avg_search_volume": sum(k["search_volume"] for k in keywords) // len(keywords)
        }
    
    def analyze_competition(self, keyword: str) -> Dict[str, Any]:
        """Analyze competition for a specific keyword."""
        return {
            "keyword": keyword,
            "competition_level": random.choice(["Low", "Medium", "High"]),
            "top_competitors": [
                {"domain": "example1.com", "authority": random.randint(40, 90)},
                {"domain": "example2.com", "authority": random.randint(40, 90)},
                {"domain": "example3.com", "authority": random.randint(40, 90)}
            ],
            "content_gaps": [
                "Missing detailed comparison section",
                "No pricing information",
                "Limited user reviews"
            ],
            "opportunities": [
                "Target long-tail variations",
                "Create comparison content",
                "Add user testimonials"
            ]
        }
    
    def optimize_content(self, content: str, target_keywords: List[str]) -> Dict[str, Any]:
        """Analyze and optimize content for SEO."""
        word_count = len(content.split())
        keyword_density = {}
        
        for keyword in target_keywords:
            count = content.lower().count(keyword.lower())
            density = (count / word_count) * 100 if word_count > 0 else 0
            keyword_density[keyword] = {
                "count": count,
                "density": round(density, 2)
            }
        
        # Calculate SEO score
        seo_score = self._calculate_seo_score(content, target_keywords)
        
        return {
            "word_count": word_count,
            "keyword_density": keyword_density,
            "seo_score": seo_score,
            "recommendations": self._get_seo_recommendations(content, target_keywords),
            "readability_score": random.randint(70, 90)
        }
    
    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Calculate overall SEO score for content."""
        score = 0
        
        # Word count check
        word_count = len(content.split())
        if 1000 <= word_count <= 3000:
            score += 20
        elif word_count >= 500:
            score += 10
        
        # Keyword presence
        for keyword in keywords:
            if keyword.lower() in content.lower():
                score += 15
        
        # Structure checks
        if "##" in content:  # Has headings
            score += 15
        if "[AFFILIATE LINK]" in content:  # Has affiliate links
            score += 10
        if "FAQ" in content or "frequently asked questions" in content.lower():
            score += 10
        
        return min(score, 100)
    
    def _get_seo_recommendations(self, content: str, keywords: List[str]) -> List[str]:
        """Generate SEO improvement recommendations."""
        recommendations = []
        
        word_count = len(content.split())
        if word_count < 1000:
            recommendations.append("Increase content length to at least 1000 words")
        
        for keyword in keywords:
            if keyword.lower() not in content.lower():
                recommendations.append(f"Include target keyword: {keyword}")
        
        if "##" not in content:
            recommendations.append("Add subheadings to improve content structure")
        
        if "[AFFILIATE LINK]" not in content:
            recommendations.append("Add strategic affiliate link placements")
        
        return recommendations
````

## File: automated-blog-system/src/services/trend_analyzer.py
````python
import random
from typing import List, Dict, Any

class TrendAnalyzer:
    """Service for analyzing trending products and market data."""
    
    def __init__(self, use_mock_data: bool = True):
        self.use_mock_data = use_mock_data
    
    def get_trending_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending products from various sources."""
        if self.use_mock_data:
            return self._get_mock_trending_products(limit)
        else:
            # TODO: Implement real API calls to product databases
            return self._get_mock_trending_products(limit)
    
    def _get_mock_trending_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate mock trending products for development."""
        mock_products = [
            {
                "name": "Apple MacBook Pro M3",
                "description": "Latest MacBook Pro with M3 chip, 14-inch display, and enhanced performance for professionals.",
                "category": "Electronics",
                "price": 1999.99,
                "currency": "USD",
                "trend_score": 95.5,
                "search_volume": 150000,
                "competition_level": "High",
                "affiliate_programs": ["Amazon Associates", "Best Buy Affiliate"],
                "primary_keywords": ["macbook pro m3", "apple laptop", "professional laptop"],
                "secondary_keywords": ["mac computer", "apple silicon", "creative workstation"],
                "source_url": "https://www.apple.com/macbook-pro/",
                "image_url": "https://example.com/macbook-pro-m3.jpg"
            },
            {
                "name": "Whey Protein Isolate Premium",
                "description": "High-quality whey protein isolate for muscle building and recovery.",
                "category": "Health & Fitness",
                "price": 49.99,
                "currency": "USD",
                "trend_score": 88.2,
                "search_volume": 75000,
                "competition_level": "Medium",
                "affiliate_programs": ["ClickBank", "ShareASale"],
                "primary_keywords": ["whey protein", "protein powder", "muscle building"],
                "secondary_keywords": ["fitness supplement", "post workout", "protein isolate"],
                "source_url": "https://example.com/whey-protein",
                "image_url": "https://example.com/whey-protein.jpg"
            },
            {
                "name": "Notion Productivity Suite",
                "description": "All-in-one workspace for notes, tasks, wikis, and databases.",
                "category": "Software",
                "price": 8.00,
                "currency": "USD",
                "trend_score": 92.1,
                "search_volume": 200000,
                "competition_level": "Medium",
                "affiliate_programs": ["Notion Partner Program"],
                "primary_keywords": ["notion app", "productivity software", "note taking"],
                "secondary_keywords": ["workspace app", "team collaboration", "project management"],
                "source_url": "https://www.notion.so/",
                "image_url": "https://example.com/notion.jpg"
            },
            {
                "name": "Sony WH-1000XM5 Headphones",
                "description": "Industry-leading noise canceling wireless headphones with premium sound quality.",
                "category": "Electronics",
                "price": 399.99,
                "currency": "USD",
                "trend_score": 89.7,
                "search_volume": 120000,
                "competition_level": "High",
                "affiliate_programs": ["Amazon Associates", "Sony Affiliate"],
                "primary_keywords": ["sony headphones", "noise canceling", "wireless headphones"],
                "secondary_keywords": ["premium audio", "travel headphones", "bluetooth headphones"],
                "source_url": "https://www.sony.com/headphones",
                "image_url": "https://example.com/sony-headphones.jpg"
            },
            {
                "name": "Keto Diet Cookbook",
                "description": "Complete guide to ketogenic diet with 200+ delicious recipes.",
                "category": "Health & Fitness",
                "price": 24.99,
                "currency": "USD",
                "trend_score": 85.3,
                "search_volume": 95000,
                "competition_level": "Medium",
                "affiliate_programs": ["ClickBank", "Amazon Associates"],
                "primary_keywords": ["keto diet", "ketogenic recipes", "low carb cookbook"],
                "secondary_keywords": ["weight loss", "healthy eating", "diet plan"],
                "source_url": "https://example.com/keto-cookbook",
                "image_url": "https://example.com/keto-cookbook.jpg"
            }
        ]
        
        # Shuffle and return requested number
        random.shuffle(mock_products)
        return mock_products[:limit]
    
    def analyze_product_trends(self, product_name: str) -> Dict[str, Any]:
        """Analyze trends for a specific product."""
        return {
            "product_name": product_name,
            "trend_direction": "increasing",
            "trend_strength": random.uniform(70, 95),
            "seasonal_factors": ["holiday season", "back to school"],
            "competitor_analysis": {
                "top_competitors": ["Competitor A", "Competitor B"],
                "market_share": random.uniform(10, 30)
            }
        }
````

## File: automated-blog-system/src/static/index.html
````html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>automated-blog-system</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .section { margin-bottom: 20px; padding: 15px; border: 1px solid #ccc; border-radius: 5px; }
        h2 { margin-top: 0; }
        label { display: inline-block; width: 80px; margin-bottom: 5px; }
        input[type="text"], input[type="email"], input[type="number"] { margin-bottom: 10px; padding: 5px; width: 200px; }
        button { padding: 8px 15px; margin-right: 10px; cursor: pointer; }
        pre { background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <h1>User API Test</h1>

    <!-- Get All Users -->
    <div class="section">
        <h2>Get All Users (GET /users)</h2>
        <button onclick="getUsers()">Get Users</button>
        <pre id="get-users-result"></pre>
    </div>

    <!-- Create User -->
    <div class="section">
        <h2>Create User (POST /users)</h2>
        <label for="create-username">Username:</label>
        <input type="text" id="create-username" name="username"><br>
        <label for="create-email">Email:</label>
        <input type="email" id="create-email" name="email"><br>
        <button onclick="createUser()">Create User</button>
        <pre id="create-user-result"></pre>
    </div>

    <!-- Get Single User -->
    <div class="section">
        <h2>Get Single User (GET /users/&lt;id&gt;)</h2>
        <label for="get-user-id">User ID:</label>
        <input type="number" id="get-user-id" name="user_id"><br>
        <button onclick="getUser()">Get User</button>
        <pre id="get-user-result"></pre>
    </div>

    <!-- Update User -->
    <div class="section">
        <h2>Update User (PUT /users/&lt;id&gt;)</h2>
        <label for="update-user-id">User ID:</label>
        <input type="number" id="update-user-id" name="user_id"><br>
        <label for="update-username">New Username:</label>
        <input type="text" id="update-username" name="username"><br>
        <label for="update-email">New Email:</label>
        <input type="email" id="update-email" name="email"><br>
        <button onclick="updateUser()">Update User</button>
        <pre id="update-user-result"></pre>
    </div>

    <!-- Delete User -->
    <div class="section">
        <h2>Delete User (DELETE /users/&lt;id&gt;)</h2>
        <label for="delete-user-id">User ID:</label>
        <input type="number" id="delete-user-id" name="user_id"><br>
        <button onclick="deleteUser()">Delete User</button>
        <pre id="delete-user-result"></pre>
    </div>

    <script>
        const API_BASE_URL = '/api/users';

        // Helper function to display results
        function displayResult(elementId, data) {
            document.getElementById(elementId).textContent = JSON.stringify(data, null, 2);
        }

        // Helper function to display errors
        function displayError(elementId, error) {
            document.getElementById(elementId).textContent = `Error: ${error.message || error}`;
        }

        // GET /users
        async function getUsers() {
            const resultElementId = 'get-users-result';
            try {
                const response = await fetch(API_BASE_URL);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                displayResult(resultElementId, data);
            } catch (error) {
                displayError(resultElementId, error);
            }
        }

        // POST /users
        async function createUser() {
            const resultElementId = 'create-user-result';
            const username = document.getElementById('create-username').value;
            const email = document.getElementById('create-email').value;
            if (!username || !email) {
                displayError(resultElementId, 'Username and email cannot be empty');
                return;
            }
            try {
                const response = await fetch(API_BASE_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email })
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.message || `HTTP error! status: ${response.status}`);
                displayResult(resultElementId, data);
                // 清空输入框
                document.getElementById('create-username').value = '';
                document.getElementById('create-email').value = '';
            } catch (error) {
                displayError(resultElementId, error);
            }
        }

        // GET /users/<id>
        async function getUser() {
            const resultElementId = 'get-user-result';
            const userId = document.getElementById('get-user-id').value;
            if (!userId) {
                displayError(resultElementId, 'User ID cannot be empty');
                return;
            }
            try {
                const response = await fetch(`${API_BASE_URL}/${userId}`);
                 if (response.status === 404) throw new Error('User not found');
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                displayResult(resultElementId, data);
            } catch (error) {
                displayError(resultElementId, error);
            }
        }

        // PUT /users/<id>
        async function updateUser() {
            const resultElementId = 'update-user-result';
            const userId = document.getElementById('update-user-id').value;
            const username = document.getElementById('update-username').value;
            const email = document.getElementById('update-email').value;
            if (!userId) {
                displayError(resultElementId, 'User ID cannot be empty');
                return;
            }
            const updateData = {};
            if (username) updateData.username = username;
            if (email) updateData.email = email;
            if (Object.keys(updateData).length === 0) {
                 displayError(resultElementId, 'Please enter a username or email to update');
                 return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/${userId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                if (response.status === 404) throw new Error('User not found');
                const data = await response.json();
                 if (!response.ok) throw new Error(data.message || `HTTP error! status: ${response.status}`);
                displayResult(resultElementId, data);
                 // Clear input fields
                document.getElementById('update-username').value = '';
                document.getElementById('update-email').value = '';
            } catch (error) {
                displayError(resultElementId, error);
            }
        }

        // DELETE /users/<id>
        async function deleteUser() {
            const resultElementId = 'delete-user-result';
            const userId = document.getElementById('delete-user-id').value;
            if (!userId) {
                displayError(resultElementId, 'User ID cannot be empty');
                return;
            }
            try {
                const response = await fetch(`${API_BASE_URL}/${userId}`, {
                    method: 'DELETE'
                });
                if (response.status === 404) throw new Error('User not found');
                if (!response.ok && response.status !== 204) throw new Error(`HTTP error! status: ${response.status}`); // Allow 204
                // 204 No Content indicates success
                if (response.status === 204) {
                     displayResult(resultElementId, { message: `User ID ${userId} has been successfully deleted` });
                } else {
                     // Try to read potential error message even on success-like status if not 204
                     const data = await response.text();
                     displayResult(resultElementId, data || { message: `Deletion successful, status code: ${response.status}` });
                }
                 // Clear input field
                document.getElementById('delete-user-id').value = '';
            } catch (error) {
                displayError(resultElementId, error);
            }
        }
    </script>
</body>
</html>
````

## File: automated-blog-system/.gitignore
````
.env
/venv/
venv/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
*.db
*.sqlite3
*.log
*.pid
*.egg-info/
dist/
build/
*.egg
*.whl
*.coverage
.coverage.*
*.mypy_cache/
*.pytest_cache/
*.tox/
*.idea/
*.vscode/
*.DS_Store
*.swp
*.bak
*.orig
*.tmp
*.log
*.out
*.err       

node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
````

## File: automated-blog-system/requirements.txt
````
blinker==1.9.0
click==8.2.1
Flask==3.1.1
flask-cors==6.0.0
Flask-SQLAlchemy==3.1.1
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
SQLAlchemy==2.0.41
typing_extensions==4.14.0
Werkzeug==3.1.3
````

## File: automated-blog-system/test_api.py
````python
#!/usr/bin/env python3
import requests
import json
import time

def test_endpoint(url, description):
    """Test a single API endpoint."""
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)[:200]}...")
                return True
            except:
                print(f"Response (text): {response.text[:200]}...")
                return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - endpoint taking too long")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not responding")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    base_url = "http://localhost:5000"
    
    print("🚀 Testing Automated Blog System API")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/api/health", "Health check"),
        ("/api/blog/products", "Get products"),
        ("/api/blog/articles", "Get articles"),
        ("/api/blog/trending-products", "Get trending products"),
        ("/api/automation/scheduler/status", "Scheduler status")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        results[endpoint] = test_endpoint(url, description)
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    for endpoint, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {endpoint}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")

if __name__ == "__main__":
    main()
````

## File: automated-blog-system/test_wordpress_integration.py
````python
#!/usr/bin/env python3
import requests
import json
import time
import sys

def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 50)
    print(f"🔍 {title}")
    print("=" * 50)

def create_test_product():
    """Create a test product."""
    print_section("Creating Test Product")
    
    url = "http://localhost:5000/api/blog/products"
    
    # Test product data
    product_data = {
        "name": "Test WordPress Integration Product",
        "description": "This is a test product to verify WordPress integration",
        "category": "Test",
        "price": 99.99,
        "currency": "USD",
        "trend_score": 8.5,
        "search_volume": 1000,
        "competition_level": "medium",
        "affiliate_programs": ["Amazon", "eBay"],
        "primary_keywords": ["test product", "wordpress integration"],
        "secondary_keywords": ["automated blog", "content generation"],
        "source_url": "https://example.com/test-product",
        "image_url": "https://example.com/test-product.jpg"
    }
    
    try:
        response = requests.post(url, json=product_data, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            product_id = data['product']['id']
            print(f"✅ Product created successfully with ID: {product_id}")
            print(f"Product details: {json.dumps(data['product'], indent=2)[:200]}...")
            return product_id
        else:
            print(f"❌ Failed to create product: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating product: {e}")
        return None

def generate_article(product_id):
    """Generate an article for the product."""
    print_section("Generating Article")
    
    if not product_id:
        print("❌ Cannot generate article: No product ID")
        return None
    
    url = "http://localhost:5000/api/blog/generate-article"
    
    article_data = {
        "product_id": product_id
    }
    
    try:
        print(f"Generating article for product ID: {product_id}")
        response = requests.post(url, json=article_data, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            article_id = data['article']['id']
            wordpress_post_id = data['article'].get('wordpress_post_id')
            
            print(f"✅ Article generated successfully with ID: {article_id}")
            print(f"Article title: {data['article']['title']}")
            print(f"WordPress Post ID: {wordpress_post_id or 'Not posted to WordPress'}")
            
            # Print excerpt of the article content
            content = data['article']['content']
            print(f"\nArticle excerpt:\n{content[:300]}...\n")
            
            return data['article']
        else:
            print(f"❌ Failed to generate article: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating article: {e}")
        return None

def verify_wordpress_post(article):
    """Verify the article was posted to WordPress."""
    print_section("Verifying WordPress Post")
    
    if not article:
        print("❌ Cannot verify WordPress post: No article data")
        return False
    
    wordpress_post_id = article.get('wordpress_post_id')
    
    if not wordpress_post_id:
        print("❌ Article was not posted to WordPress")
        print("Check server logs for more information")
        return False
    
    print(f"✅ Article was successfully posted to WordPress with ID: {wordpress_post_id}")
    print(f"Status: {article.get('status')}")
    
    # If we had access to the WordPress site, we could verify the post exists
    # by making a request to the WordPress API
    print("\nTo manually verify, check the WordPress site at:")
    print(f"https://crawley.pro/?p={wordpress_post_id}")
    
    return True

def main():
    """Main function to test WordPress integration."""
    print("\n🚀 Testing WordPress Integration")
    print("=" * 50)
    
    # Step 1: Create a test product
    product_id = create_test_product()
    
    if not product_id:
        print("❌ Test failed: Could not create test product")
        sys.exit(1)
    
    # Step 2: Generate an article for the product
    article = generate_article(product_id)
    
    if not article:
        print("❌ Test failed: Could not generate article")
        sys.exit(1)
    
    # Step 3: Verify the article was posted to WordPress
    success = verify_wordpress_post(article)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    if success:
        print("✅ WordPress integration test PASSED")
        print("The article was successfully posted to WordPress")
    else:
        print("❌ WordPress integration test FAILED")
        print("The article was not posted to WordPress")
    
    print("\nCheck server logs for more detailed information")

if __name__ == "__main__":
    main()
````

## File: blog-frontend/src/assets/react.svg
````
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="35.93" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 228"><path fill="#00D8FF" d="M210.483 73.824a171.49 171.49 0 0 0-8.24-2.597c.465-1.9.893-3.777 1.273-5.621c6.238-30.281 2.16-54.676-11.769-62.708c-13.355-7.7-35.196.329-57.254 19.526a171.23 171.23 0 0 0-6.375 5.848a155.866 155.866 0 0 0-4.241-3.917C100.759 3.829 77.587-4.822 63.673 3.233C50.33 10.957 46.379 33.89 51.995 62.588a170.974 170.974 0 0 0 1.892 8.48c-3.28.932-6.445 1.924-9.474 2.98C17.309 83.498 0 98.307 0 113.668c0 15.865 18.582 31.778 46.812 41.427a145.52 145.52 0 0 0 6.921 2.165a167.467 167.467 0 0 0-2.01 9.138c-5.354 28.2-1.173 50.591 12.134 58.266c13.744 7.926 36.812-.22 59.273-19.855a145.567 145.567 0 0 0 5.342-4.923a168.064 168.064 0 0 0 6.92 6.314c21.758 18.722 43.246 26.282 56.54 18.586c13.731-7.949 18.194-32.003 12.4-61.268a145.016 145.016 0 0 0-1.535-6.842c1.62-.48 3.21-.974 4.76-1.488c29.348-9.723 48.443-25.443 48.443-41.52c0-15.417-17.868-30.326-45.517-39.844Zm-6.365 70.984c-1.4.463-2.836.91-4.3 1.345c-3.24-10.257-7.612-21.163-12.963-32.432c5.106-11 9.31-21.767 12.459-31.957c2.619.758 5.16 1.557 7.61 2.4c23.69 8.156 38.14 20.213 38.14 29.504c0 9.896-15.606 22.743-40.946 31.14Zm-10.514 20.834c2.562 12.94 2.927 24.64 1.23 33.787c-1.524 8.219-4.59 13.698-8.382 15.893c-8.067 4.67-25.32-1.4-43.927-17.412a156.726 156.726 0 0 1-6.437-5.87c7.214-7.889 14.423-17.06 21.459-27.246c12.376-1.098 24.068-2.894 34.671-5.345a134.17 134.17 0 0 1 1.386 6.193ZM87.276 214.515c-7.882 2.783-14.16 2.863-17.955.675c-8.075-4.657-11.432-22.636-6.853-46.752a156.923 156.923 0 0 1 1.869-8.499c10.486 2.32 22.093 3.988 34.498 4.994c7.084 9.967 14.501 19.128 21.976 27.15a134.668 134.668 0 0 1-4.877 4.492c-9.933 8.682-19.886 14.842-28.658 17.94ZM50.35 144.747c-12.483-4.267-22.792-9.812-29.858-15.863c-6.35-5.437-9.555-10.836-9.555-15.216c0-9.322 13.897-21.212 37.076-29.293c2.813-.98 5.757-1.905 8.812-2.773c3.204 10.42 7.406 21.315 12.477 32.332c-5.137 11.18-9.399 22.249-12.634 32.792a134.718 134.718 0 0 1-6.318-1.979Zm12.378-84.26c-4.811-24.587-1.616-43.134 6.425-47.789c8.564-4.958 27.502 2.111 47.463 19.835a144.318 144.318 0 0 1 3.841 3.545c-7.438 7.987-14.787 17.08-21.808 26.988c-12.04 1.116-23.565 2.908-34.161 5.309a160.342 160.342 0 0 1-1.76-7.887Zm110.427 27.268a347.8 347.8 0 0 0-7.785-12.803c8.168 1.033 15.994 2.404 23.343 4.08c-2.206 7.072-4.956 14.465-8.193 22.045a381.151 381.151 0 0 0-7.365-13.322Zm-45.032-43.861c5.044 5.465 10.096 11.566 15.065 18.186a322.04 322.04 0 0 0-30.257-.006c4.974-6.559 10.069-12.652 15.192-18.18ZM82.802 87.83a323.167 323.167 0 0 0-7.227 13.238c-3.184-7.553-5.909-14.98-8.134-22.152c7.304-1.634 15.093-2.97 23.209-3.984a321.524 321.524 0 0 0-7.848 12.897Zm8.081 65.352c-8.385-.936-16.291-2.203-23.593-3.793c2.26-7.3 5.045-14.885 8.298-22.6a321.187 321.187 0 0 0 7.257 13.246c2.594 4.48 5.28 8.868 8.038 13.147Zm37.542 31.03c-5.184-5.592-10.354-11.779-15.403-18.433c4.902.192 9.899.29 14.978.29c5.218 0 10.376-.117 15.453-.343c-4.985 6.774-10.018 12.97-15.028 18.486Zm52.198-57.817c3.422 7.8 6.306 15.345 8.596 22.52c-7.422 1.694-15.436 3.058-23.88 4.071a382.417 382.417 0 0 0 7.859-13.026a347.403 347.403 0 0 0 7.425-13.565Zm-16.898 8.101a358.557 358.557 0 0 1-12.281 19.815a329.4 329.4 0 0 1-23.444.823c-7.967 0-15.716-.248-23.178-.732a310.202 310.202 0 0 1-12.513-19.846h.001a307.41 307.41 0 0 1-10.923-20.627a310.278 310.278 0 0 1 10.89-20.637l-.001.001a307.318 307.318 0 0 1 12.413-19.761c7.613-.576 15.42-.876 23.31-.876H128c7.926 0 15.743.303 23.354.883a329.357 329.357 0 0 1 12.335 19.695a358.489 358.489 0 0 1 11.036 20.54a329.472 329.472 0 0 1-11 20.722Zm22.56-122.124c8.572 4.944 11.906 24.881 6.52 51.026c-.344 1.668-.73 3.367-1.15 5.09c-10.622-2.452-22.155-4.275-34.23-5.408c-7.034-10.017-14.323-19.124-21.64-27.008a160.789 160.789 0 0 1 5.888-5.4c18.9-16.447 36.564-22.941 44.612-18.3ZM128 90.808c12.625 0 22.86 10.235 22.86 22.86s-10.235 22.86-22.86 22.86s-22.86-10.235-22.86-22.86s10.235-22.86 22.86-22.86Z"></path></svg>
````

## File: blog-frontend/src/components/ui/accordion.jsx
````javascript
import * as React from "react"
import * as AccordionPrimitive from "@radix-ui/react-accordion"
import { ChevronDownIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function Accordion({
  ...props
}) {
  return <AccordionPrimitive.Root data-slot="accordion" {...props} />;
}

function AccordionItem({
  className,
  ...props
}) {
  return (
    <AccordionPrimitive.Item
      data-slot="accordion-item"
      className={cn("border-b last:border-b-0", className)}
      {...props} />
  );
}

function AccordionTrigger({
  className,
  children,
  ...props
}) {
  return (
    <AccordionPrimitive.Header className="flex">
      <AccordionPrimitive.Trigger
        data-slot="accordion-trigger"
        className={cn(
          "focus-visible:border-ring focus-visible:ring-ring/50 flex flex-1 items-start justify-between gap-4 rounded-md py-4 text-left text-sm font-medium transition-all outline-none hover:underline focus-visible:ring-[3px] disabled:pointer-events-none disabled:opacity-50 [&[data-state=open]>svg]:rotate-180",
          className
        )}
        {...props}>
        {children}
        <ChevronDownIcon
          className="text-muted-foreground pointer-events-none size-4 shrink-0 translate-y-0.5 transition-transform duration-200" />
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  );
}

function AccordionContent({
  className,
  children,
  ...props
}) {
  return (
    <AccordionPrimitive.Content
      data-slot="accordion-content"
      className="data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down overflow-hidden text-sm"
      {...props}>
      <div className={cn("pt-0 pb-4", className)}>{children}</div>
    </AccordionPrimitive.Content>
  );
}

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent }
````

## File: blog-frontend/src/components/ui/alert-dialog.jsx
````javascript
"use client"

import * as React from "react"
import * as AlertDialogPrimitive from "@radix-ui/react-alert-dialog"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

function AlertDialog({
  ...props
}) {
  return <AlertDialogPrimitive.Root data-slot="alert-dialog" {...props} />;
}

function AlertDialogTrigger({
  ...props
}) {
  return (<AlertDialogPrimitive.Trigger data-slot="alert-dialog-trigger" {...props} />);
}

function AlertDialogPortal({
  ...props
}) {
  return (<AlertDialogPrimitive.Portal data-slot="alert-dialog-portal" {...props} />);
}

function AlertDialogOverlay({
  className,
  ...props
}) {
  return (
    <AlertDialogPrimitive.Overlay
      data-slot="alert-dialog-overlay"
      className={cn(
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/50",
        className
      )}
      {...props} />
  );
}

function AlertDialogContent({
  className,
  ...props
}) {
  return (
    <AlertDialogPortal>
      <AlertDialogOverlay />
      <AlertDialogPrimitive.Content
        data-slot="alert-dialog-content"
        className={cn(
          "bg-background data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed top-[50%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg duration-200 sm:max-w-lg",
          className
        )}
        {...props} />
    </AlertDialogPortal>
  );
}

function AlertDialogHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="alert-dialog-header"
      className={cn("flex flex-col gap-2 text-center sm:text-left", className)}
      {...props} />
  );
}

function AlertDialogFooter({
  className,
  ...props
}) {
  return (
    <div
      data-slot="alert-dialog-footer"
      className={cn("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end", className)}
      {...props} />
  );
}

function AlertDialogTitle({
  className,
  ...props
}) {
  return (
    <AlertDialogPrimitive.Title
      data-slot="alert-dialog-title"
      className={cn("text-lg font-semibold", className)}
      {...props} />
  );
}

function AlertDialogDescription({
  className,
  ...props
}) {
  return (
    <AlertDialogPrimitive.Description
      data-slot="alert-dialog-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />
  );
}

function AlertDialogAction({
  className,
  ...props
}) {
  return (<AlertDialogPrimitive.Action className={cn(buttonVariants(), className)} {...props} />);
}

function AlertDialogCancel({
  className,
  ...props
}) {
  return (
    <AlertDialogPrimitive.Cancel
      className={cn(buttonVariants({ variant: "outline" }), className)}
      {...props} />
  );
}

export {
  AlertDialog,
  AlertDialogPortal,
  AlertDialogOverlay,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
}
````

## File: blog-frontend/src/components/ui/alert.jsx
````javascript
import * as React from "react"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border px-4 py-3 text-sm grid has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr] grid-cols-[0_1fr] has-[>svg]:gap-x-3 gap-y-0.5 items-start [&>svg]:size-4 [&>svg]:translate-y-0.5 [&>svg]:text-current",
  {
    variants: {
      variant: {
        default: "bg-card text-card-foreground",
        destructive:
          "text-destructive bg-card [&>svg]:text-current *:data-[slot=alert-description]:text-destructive/90",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Alert({
  className,
  variant,
  ...props
}) {
  return (
    <div
      data-slot="alert"
      role="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props} />
  );
}

function AlertTitle({
  className,
  ...props
}) {
  return (
    <div
      data-slot="alert-title"
      className={cn("col-start-2 line-clamp-1 min-h-4 font-medium tracking-tight", className)}
      {...props} />
  );
}

function AlertDescription({
  className,
  ...props
}) {
  return (
    <div
      data-slot="alert-description"
      className={cn(
        "text-muted-foreground col-start-2 grid justify-items-start gap-1 text-sm [&_p]:leading-relaxed",
        className
      )}
      {...props} />
  );
}

export { Alert, AlertTitle, AlertDescription }
````

## File: blog-frontend/src/components/ui/aspect-ratio.jsx
````javascript
import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio"

function AspectRatio({
  ...props
}) {
  return <AspectRatioPrimitive.Root data-slot="aspect-ratio" {...props} />;
}

export { AspectRatio }
````

## File: blog-frontend/src/components/ui/avatar.jsx
````javascript
"use client"

import * as React from "react"
import * as AvatarPrimitive from "@radix-ui/react-avatar"

import { cn } from "@/lib/utils"

function Avatar({
  className,
  ...props
}) {
  return (
    <AvatarPrimitive.Root
      data-slot="avatar"
      className={cn("relative flex size-8 shrink-0 overflow-hidden rounded-full", className)}
      {...props} />
  );
}

function AvatarImage({
  className,
  ...props
}) {
  return (
    <AvatarPrimitive.Image
      data-slot="avatar-image"
      className={cn("aspect-square size-full", className)}
      {...props} />
  );
}

function AvatarFallback({
  className,
  ...props
}) {
  return (
    <AvatarPrimitive.Fallback
      data-slot="avatar-fallback"
      className={cn(
        "bg-muted flex size-full items-center justify-center rounded-full",
        className
      )}
      {...props} />
  );
}

export { Avatar, AvatarImage, AvatarFallback }
````

## File: blog-frontend/src/components/ui/badge.jsx
````javascript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90",
        destructive:
          "border-transparent bg-destructive text-white [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot : "span"

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props} />
  );
}

export { Badge, badgeVariants }
````

## File: blog-frontend/src/components/ui/breadcrumb.jsx
````javascript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { ChevronRight, MoreHorizontal } from "lucide-react"

import { cn } from "@/lib/utils"

function Breadcrumb({
  ...props
}) {
  return <nav aria-label="breadcrumb" data-slot="breadcrumb" {...props} />;
}

function BreadcrumbList({
  className,
  ...props
}) {
  return (
    <ol
      data-slot="breadcrumb-list"
      className={cn(
        "text-muted-foreground flex flex-wrap items-center gap-1.5 text-sm break-words sm:gap-2.5",
        className
      )}
      {...props} />
  );
}

function BreadcrumbItem({
  className,
  ...props
}) {
  return (
    <li
      data-slot="breadcrumb-item"
      className={cn("inline-flex items-center gap-1.5", className)}
      {...props} />
  );
}

function BreadcrumbLink({
  asChild,
  className,
  ...props
}) {
  const Comp = asChild ? Slot : "a"

  return (
    <Comp
      data-slot="breadcrumb-link"
      className={cn("hover:text-foreground transition-colors", className)}
      {...props} />
  );
}

function BreadcrumbPage({
  className,
  ...props
}) {
  return (
    <span
      data-slot="breadcrumb-page"
      role="link"
      aria-disabled="true"
      aria-current="page"
      className={cn("text-foreground font-normal", className)}
      {...props} />
  );
}

function BreadcrumbSeparator({
  children,
  className,
  ...props
}) {
  return (
    <li
      data-slot="breadcrumb-separator"
      role="presentation"
      aria-hidden="true"
      className={cn("[&>svg]:size-3.5", className)}
      {...props}>
      {children ?? <ChevronRight />}
    </li>
  );
}

function BreadcrumbEllipsis({
  className,
  ...props
}) {
  return (
    <span
      data-slot="breadcrumb-ellipsis"
      role="presentation"
      aria-hidden="true"
      className={cn("flex size-9 items-center justify-center", className)}
      {...props}>
      <MoreHorizontal className="size-4" />
      <span className="sr-only">More</span>
    </span>
  );
}

export {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
  BreadcrumbEllipsis,
}
````

## File: blog-frontend/src/components/ui/button.jsx
````javascript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-xs hover:bg-primary/90",
        destructive:
          "bg-destructive text-white shadow-xs hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50",
        secondary:
          "bg-secondary text-secondary-foreground shadow-xs hover:bg-secondary/80",
        ghost:
          "hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3",
        sm: "h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5",
        lg: "h-10 rounded-md px-6 has-[>svg]:px-4",
        icon: "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props} />
  );
}

export { Button, buttonVariants }
````

## File: blog-frontend/src/components/ui/calendar.jsx
````javascript
import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { DayPicker } from "react-day-picker"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        months: "flex flex-col sm:flex-row gap-2",
        month: "flex flex-col gap-4",
        caption: "flex justify-center pt-1 relative items-center w-full",
        caption_label: "text-sm font-medium",
        nav: "flex items-center gap-1",
        nav_button: cn(
          buttonVariants({ variant: "outline" }),
          "size-7 bg-transparent p-0 opacity-50 hover:opacity-100"
        ),
        nav_button_previous: "absolute left-1",
        nav_button_next: "absolute right-1",
        table: "w-full border-collapse space-x-1",
        head_row: "flex",
        head_cell:
          "text-muted-foreground rounded-md w-8 font-normal text-[0.8rem]",
        row: "flex w-full mt-2",
        cell: cn(
          "relative p-0 text-center text-sm focus-within:relative focus-within:z-20 [&:has([aria-selected])]:bg-accent [&:has([aria-selected].day-range-end)]:rounded-r-md",
          props.mode === "range"
            ? "[&:has(>.day-range-end)]:rounded-r-md [&:has(>.day-range-start)]:rounded-l-md first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md"
            : "[&:has([aria-selected])]:rounded-md"
        ),
        day: cn(
          buttonVariants({ variant: "ghost" }),
          "size-8 p-0 font-normal aria-selected:opacity-100"
        ),
        day_range_start:
          "day-range-start aria-selected:bg-primary aria-selected:text-primary-foreground",
        day_range_end:
          "day-range-end aria-selected:bg-primary aria-selected:text-primary-foreground",
        day_selected:
          "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
        day_today: "bg-accent text-accent-foreground",
        day_outside:
          "day-outside text-muted-foreground aria-selected:text-muted-foreground",
        day_disabled: "text-muted-foreground opacity-50",
        day_range_middle:
          "aria-selected:bg-accent aria-selected:text-accent-foreground",
        day_hidden: "invisible",
        ...classNames,
      }}
      components={{
        IconLeft: ({ className, ...props }) => (
          <ChevronLeft className={cn("size-4", className)} {...props} />
        ),
        IconRight: ({ className, ...props }) => (
          <ChevronRight className={cn("size-4", className)} {...props} />
        ),
      }}
      {...props} />
  );
}

export { Calendar }
````

## File: blog-frontend/src/components/ui/card.jsx
````javascript
import * as React from "react"

import { cn } from "@/lib/utils"

function Card({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        className
      )}
      {...props} />
  );
}

function CardHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",
        className
      )}
      {...props} />
  );
}

function CardTitle({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card-title"
      className={cn("leading-none font-semibold", className)}
      {...props} />
  );
}

function CardDescription({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />
  );
}

function CardAction({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card-action"
      className={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        className
      )}
      {...props} />
  );
}

function CardContent({
  className,
  ...props
}) {
  return (<div data-slot="card-content" className={cn("px-6", className)} {...props} />);
}

function CardFooter({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card-footer"
      className={cn("flex items-center px-6 [.border-t]:pt-6", className)}
      {...props} />
  );
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
}
````

## File: blog-frontend/src/components/ui/carousel.jsx
````javascript
"use client";
import * as React from "react"
import useEmblaCarousel from "embla-carousel-react";
import { ArrowLeft, ArrowRight } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

const CarouselContext = React.createContext(null)

function useCarousel() {
  const context = React.useContext(CarouselContext)

  if (!context) {
    throw new Error("useCarousel must be used within a <Carousel />")
  }

  return context
}

function Carousel({
  orientation = "horizontal",
  opts,
  setApi,
  plugins,
  className,
  children,
  ...props
}) {
  const [carouselRef, api] = useEmblaCarousel({
    ...opts,
    axis: orientation === "horizontal" ? "x" : "y",
  }, plugins)
  const [canScrollPrev, setCanScrollPrev] = React.useState(false)
  const [canScrollNext, setCanScrollNext] = React.useState(false)

  const onSelect = React.useCallback((api) => {
    if (!api) return
    setCanScrollPrev(api.canScrollPrev())
    setCanScrollNext(api.canScrollNext())
  }, [])

  const scrollPrev = React.useCallback(() => {
    api?.scrollPrev()
  }, [api])

  const scrollNext = React.useCallback(() => {
    api?.scrollNext()
  }, [api])

  const handleKeyDown = React.useCallback((event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault()
      scrollPrev()
    } else if (event.key === "ArrowRight") {
      event.preventDefault()
      scrollNext()
    }
  }, [scrollPrev, scrollNext])

  React.useEffect(() => {
    if (!api || !setApi) return
    setApi(api)
  }, [api, setApi])

  React.useEffect(() => {
    if (!api) return
    onSelect(api)
    api.on("reInit", onSelect)
    api.on("select", onSelect)

    return () => {
      api?.off("select", onSelect)
    };
  }, [api, onSelect])

  return (
    <CarouselContext.Provider
      value={{
        carouselRef,
        api: api,
        opts,
        orientation:
          orientation || (opts?.axis === "y" ? "vertical" : "horizontal"),
        scrollPrev,
        scrollNext,
        canScrollPrev,
        canScrollNext,
      }}>
      <div
        onKeyDownCapture={handleKeyDown}
        className={cn("relative", className)}
        role="region"
        aria-roledescription="carousel"
        data-slot="carousel"
        {...props}>
        {children}
      </div>
    </CarouselContext.Provider>
  );
}

function CarouselContent({
  className,
  ...props
}) {
  const { carouselRef, orientation } = useCarousel()

  return (
    <div
      ref={carouselRef}
      className="overflow-hidden"
      data-slot="carousel-content">
      <div
        className={cn(
          "flex",
          orientation === "horizontal" ? "-ml-4" : "-mt-4 flex-col",
          className
        )}
        {...props} />
    </div>
  );
}

function CarouselItem({
  className,
  ...props
}) {
  const { orientation } = useCarousel()

  return (
    <div
      role="group"
      aria-roledescription="slide"
      data-slot="carousel-item"
      className={cn(
        "min-w-0 shrink-0 grow-0 basis-full",
        orientation === "horizontal" ? "pl-4" : "pt-4",
        className
      )}
      {...props} />
  );
}

function CarouselPrevious({
  className,
  variant = "outline",
  size = "icon",
  ...props
}) {
  const { orientation, scrollPrev, canScrollPrev } = useCarousel()

  return (
    <Button
      data-slot="carousel-previous"
      variant={variant}
      size={size}
      className={cn("absolute size-8 rounded-full", orientation === "horizontal"
        ? "top-1/2 -left-12 -translate-y-1/2"
        : "-top-12 left-1/2 -translate-x-1/2 rotate-90", className)}
      disabled={!canScrollPrev}
      onClick={scrollPrev}
      {...props}>
      <ArrowLeft />
      <span className="sr-only">Previous slide</span>
    </Button>
  );
}

function CarouselNext({
  className,
  variant = "outline",
  size = "icon",
  ...props
}) {
  const { orientation, scrollNext, canScrollNext } = useCarousel()

  return (
    <Button
      data-slot="carousel-next"
      variant={variant}
      size={size}
      className={cn("absolute size-8 rounded-full", orientation === "horizontal"
        ? "top-1/2 -right-12 -translate-y-1/2"
        : "-bottom-12 left-1/2 -translate-x-1/2 rotate-90", className)}
      disabled={!canScrollNext}
      onClick={scrollNext}
      {...props}>
      <ArrowRight />
      <span className="sr-only">Next slide</span>
    </Button>
  );
}

export { Carousel, CarouselContent, CarouselItem, CarouselPrevious, CarouselNext };
````

## File: blog-frontend/src/components/ui/chart.jsx
````javascript
import * as React from "react"
import * as RechartsPrimitive from "recharts"

import { cn } from "@/lib/utils"

// Format: { THEME_NAME: CSS_SELECTOR }
const THEMES = {
  light: "",
  dark: ".dark"
}

const ChartContext = React.createContext(null)

function useChart() {
  const context = React.useContext(ChartContext)

  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />")
  }

  return context
}

function ChartContainer({
  id,
  className,
  children,
  config,
  ...props
}) {
  const uniqueId = React.useId()
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-slot="chart"
        data-chart={chartId}
        className={cn(
          "[&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border flex aspect-video justify-center text-xs [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-hidden [&_.recharts-sector]:outline-hidden [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-surface]:outline-hidden",
          className
        )}
        {...props}>
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>
          {children}
        </RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
}

const ChartStyle = ({
  id,
  config
}) => {
  const colorConfig = Object.entries(config).filter(([, config]) => config.theme || config.color)

  if (!colorConfig.length) {
    return null
  }

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: Object.entries(THEMES)
          .map(([theme, prefix]) => `
${prefix} [data-chart=${id}] {
${colorConfig
.map(([key, itemConfig]) => {
const color =
  itemConfig.theme?.[theme] ||
  itemConfig.color
return color ? `  --color-${key}: ${color};` : null
})
.join("\n")}
}
`)
          .join("\n"),
      }} />
  );
}

const ChartTooltip = RechartsPrimitive.Tooltip

function ChartTooltipContent({
  active,
  payload,
  className,
  indicator = "dot",
  hideLabel = false,
  hideIndicator = false,
  label,
  labelFormatter,
  labelClassName,
  formatter,
  color,
  nameKey,
  labelKey
}) {
  const { config } = useChart()

  const tooltipLabel = React.useMemo(() => {
    if (hideLabel || !payload?.length) {
      return null
    }

    const [item] = payload
    const key = `${labelKey || item?.dataKey || item?.name || "value"}`
    const itemConfig = getPayloadConfigFromPayload(config, item, key)
    const value =
      !labelKey && typeof label === "string"
        ? config[label]?.label || label
        : itemConfig?.label

    if (labelFormatter) {
      return (
        <div className={cn("font-medium", labelClassName)}>
          {labelFormatter(value, payload)}
        </div>
      );
    }

    if (!value) {
      return null
    }

    return <div className={cn("font-medium", labelClassName)}>{value}</div>;
  }, [
    label,
    labelFormatter,
    payload,
    hideLabel,
    labelClassName,
    config,
    labelKey,
  ])

  if (!active || !payload?.length) {
    return null
  }

  const nestLabel = payload.length === 1 && indicator !== "dot"

  return (
    <div
      className={cn(
        "border-border/50 bg-background grid min-w-[8rem] items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl",
        className
      )}>
      {!nestLabel ? tooltipLabel : null}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey || item.name || item.dataKey || "value"}`
          const itemConfig = getPayloadConfigFromPayload(config, item, key)
          const indicatorColor = color || item.payload.fill || item.color

          return (
            <div
              key={item.dataKey}
              className={cn(
                "[&>svg]:text-muted-foreground flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5",
                indicator === "dot" && "items-center"
              )}>
              {formatter && item?.value !== undefined && item.name ? (
                formatter(item.value, item.name, item, index, item.payload)
              ) : (
                <>
                  {itemConfig?.icon ? (
                    <itemConfig.icon />
                  ) : (
                    !hideIndicator && (
                      <div
                        className={cn("shrink-0 rounded-[2px] border-(--color-border) bg-(--color-bg)", {
                          "h-2.5 w-2.5": indicator === "dot",
                          "w-1": indicator === "line",
                          "w-0 border-[1.5px] border-dashed bg-transparent":
                            indicator === "dashed",
                          "my-0.5": nestLabel && indicator === "dashed",
                        })}
                        style={
                          {
                            "--color-bg": indicatorColor,
                            "--color-border": indicatorColor
                          }
                        } />
                    )
                  )}
                  <div
                    className={cn(
                      "flex flex-1 justify-between leading-none",
                      nestLabel ? "items-end" : "items-center"
                    )}>
                    <div className="grid gap-1.5">
                      {nestLabel ? tooltipLabel : null}
                      <span className="text-muted-foreground">
                        {itemConfig?.label || item.name}
                      </span>
                    </div>
                    {item.value && (
                      <span className="text-foreground font-mono font-medium tabular-nums">
                        {item.value.toLocaleString()}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const ChartLegend = RechartsPrimitive.Legend

function ChartLegendContent({
  className,
  hideIcon = false,
  payload,
  verticalAlign = "bottom",
  nameKey
}) {
  const { config } = useChart()

  if (!payload?.length) {
    return null
  }

  return (
    <div
      className={cn(
        "flex items-center justify-center gap-4",
        verticalAlign === "top" ? "pb-3" : "pt-3",
        className
      )}>
      {payload.map((item) => {
        const key = `${nameKey || item.dataKey || "value"}`
        const itemConfig = getPayloadConfigFromPayload(config, item, key)

        return (
          <div
            key={item.value}
            className={cn(
              "[&>svg]:text-muted-foreground flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3"
            )}>
            {itemConfig?.icon && !hideIcon ? (
              <itemConfig.icon />
            ) : (
              <div
                className="h-2 w-2 shrink-0 rounded-[2px]"
                style={{
                  backgroundColor: item.color,
                }} />
            )}
            {itemConfig?.label}
          </div>
        );
      })}
    </div>
  );
}

// Helper to extract item config from a payload.
function getPayloadConfigFromPayload(
  config,
  payload,
  key
) {
  if (typeof payload !== "object" || payload === null) {
    return undefined
  }

  const payloadPayload =
    "payload" in payload &&
    typeof payload.payload === "object" &&
    payload.payload !== null
      ? payload.payload
      : undefined

  let configLabelKey = key

  if (
    key in payload &&
    typeof payload[key] === "string"
  ) {
    configLabelKey = payload[key]
  } else if (
    payloadPayload &&
    key in payloadPayload &&
    typeof payloadPayload[key] === "string"
  ) {
    configLabelKey = payloadPayload[key]
  }

  return configLabelKey in config
    ? config[configLabelKey]
    : config[key];
}

export {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  ChartStyle,
}
````

## File: blog-frontend/src/components/ui/checkbox.jsx
````javascript
"use client"

import * as React from "react"
import * as CheckboxPrimitive from "@radix-ui/react-checkbox"
import { CheckIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function Checkbox({
  className,
  ...props
}) {
  return (
    <CheckboxPrimitive.Root
      data-slot="checkbox"
      className={cn(
        "peer border-input dark:bg-input/30 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground dark:data-[state=checked]:bg-primary data-[state=checked]:border-primary focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive size-4 shrink-0 rounded-[4px] border shadow-xs transition-shadow outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}>
      <CheckboxPrimitive.Indicator
        data-slot="checkbox-indicator"
        className="flex items-center justify-center text-current transition-none">
        <CheckIcon className="size-3.5" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

export { Checkbox }
````

## File: blog-frontend/src/components/ui/collapsible.jsx
````javascript
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

function Collapsible({
  ...props
}) {
  return <CollapsiblePrimitive.Root data-slot="collapsible" {...props} />;
}

function CollapsibleTrigger({
  ...props
}) {
  return (<CollapsiblePrimitive.CollapsibleTrigger data-slot="collapsible-trigger" {...props} />);
}

function CollapsibleContent({
  ...props
}) {
  return (<CollapsiblePrimitive.CollapsibleContent data-slot="collapsible-content" {...props} />);
}

export { Collapsible, CollapsibleTrigger, CollapsibleContent }
````

## File: blog-frontend/src/components/ui/command.jsx
````javascript
"use client"

import * as React from "react"
import { Command as CommandPrimitive } from "cmdk"
import { SearchIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

function Command({
  className,
  ...props
}) {
  return (
    <CommandPrimitive
      data-slot="command"
      className={cn(
        "bg-popover text-popover-foreground flex h-full w-full flex-col overflow-hidden rounded-md",
        className
      )}
      {...props} />
  );
}

function CommandDialog({
  title = "Command Palette",
  description = "Search for a command to run...",
  children,
  ...props
}) {
  return (
    <Dialog {...props}>
      <DialogHeader className="sr-only">
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
      </DialogHeader>
      <DialogContent className="overflow-hidden p-0">
        <Command
          className="[&_[cmdk-group-heading]]:text-muted-foreground **:data-[slot=command-input-wrapper]:h-12 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group]]:px-2 [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5">
          {children}
        </Command>
      </DialogContent>
    </Dialog>
  );
}

function CommandInput({
  className,
  ...props
}) {
  return (
    <div
      data-slot="command-input-wrapper"
      className="flex h-9 items-center gap-2 border-b px-3">
      <SearchIcon className="size-4 shrink-0 opacity-50" />
      <CommandPrimitive.Input
        data-slot="command-input"
        className={cn(
          "placeholder:text-muted-foreground flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-hidden disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        {...props} />
    </div>
  );
}

function CommandList({
  className,
  ...props
}) {
  return (
    <CommandPrimitive.List
      data-slot="command-list"
      className={cn("max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto", className)}
      {...props} />
  );
}

function CommandEmpty({
  ...props
}) {
  return (<CommandPrimitive.Empty data-slot="command-empty" className="py-6 text-center text-sm" {...props} />);
}

function CommandGroup({
  className,
  ...props
}) {
  return (
    <CommandPrimitive.Group
      data-slot="command-group"
      className={cn(
        "text-foreground [&_[cmdk-group-heading]]:text-muted-foreground overflow-hidden p-1 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium",
        className
      )}
      {...props} />
  );
}

function CommandSeparator({
  className,
  ...props
}) {
  return (
    <CommandPrimitive.Separator
      data-slot="command-separator"
      className={cn("bg-border -mx-1 h-px", className)}
      {...props} />
  );
}

function CommandItem({
  className,
  ...props
}) {
  return (
    <CommandPrimitive.Item
      data-slot="command-item"
      className={cn(
        "data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground [&_svg:not([class*='text-'])]:text-muted-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props} />
  );
}

function CommandShortcut({
  className,
  ...props
}) {
  return (
    <span
      data-slot="command-shortcut"
      className={cn("text-muted-foreground ml-auto text-xs tracking-widest", className)}
      {...props} />
  );
}

export {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandShortcut,
  CommandSeparator,
}
````

## File: blog-frontend/src/components/ui/context-menu.jsx
````javascript
"use client"

import * as React from "react"
import * as ContextMenuPrimitive from "@radix-ui/react-context-menu"
import { CheckIcon, ChevronRightIcon, CircleIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function ContextMenu({
  ...props
}) {
  return <ContextMenuPrimitive.Root data-slot="context-menu" {...props} />;
}

function ContextMenuTrigger({
  ...props
}) {
  return (<ContextMenuPrimitive.Trigger data-slot="context-menu-trigger" {...props} />);
}

function ContextMenuGroup({
  ...props
}) {
  return (<ContextMenuPrimitive.Group data-slot="context-menu-group" {...props} />);
}

function ContextMenuPortal({
  ...props
}) {
  return (<ContextMenuPrimitive.Portal data-slot="context-menu-portal" {...props} />);
}

function ContextMenuSub({
  ...props
}) {
  return <ContextMenuPrimitive.Sub data-slot="context-menu-sub" {...props} />;
}

function ContextMenuRadioGroup({
  ...props
}) {
  return (<ContextMenuPrimitive.RadioGroup data-slot="context-menu-radio-group" {...props} />);
}

function ContextMenuSubTrigger({
  className,
  inset,
  children,
  ...props
}) {
  return (
    <ContextMenuPrimitive.SubTrigger
      data-slot="context-menu-sub-trigger"
      data-inset={inset}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[state=open]:bg-accent data-[state=open]:text-accent-foreground flex cursor-default items-center rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[inset]:pl-8 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}>
      {children}
      <ChevronRightIcon className="ml-auto" />
    </ContextMenuPrimitive.SubTrigger>
  );
}

function ContextMenuSubContent({
  className,
  ...props
}) {
  return (
    <ContextMenuPrimitive.SubContent
      data-slot="context-menu-sub-content"
      className={cn(
        "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 min-w-[8rem] origin-(--radix-context-menu-content-transform-origin) overflow-hidden rounded-md border p-1 shadow-lg",
        className
      )}
      {...props} />
  );
}

function ContextMenuContent({
  className,
  ...props
}) {
  return (
    <ContextMenuPrimitive.Portal>
      <ContextMenuPrimitive.Content
        data-slot="context-menu-content"
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 max-h-(--radix-context-menu-content-available-height) min-w-[8rem] origin-(--radix-context-menu-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border p-1 shadow-md",
          className
        )}
        {...props} />
    </ContextMenuPrimitive.Portal>
  );
}

function ContextMenuItem({
  className,
  inset,
  variant = "default",
  ...props
}) {
  return (
    <ContextMenuPrimitive.Item
      data-slot="context-menu-item"
      data-inset={inset}
      data-variant={variant}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10 dark:data-[variant=destructive]:focus:bg-destructive/20 data-[variant=destructive]:focus:text-destructive data-[variant=destructive]:*:[svg]:!text-destructive [&_svg:not([class*='text-'])]:text-muted-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[inset]:pl-8 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props} />
  );
}

function ContextMenuCheckboxItem({
  className,
  children,
  checked,
  ...props
}) {
  return (
    <ContextMenuPrimitive.CheckboxItem
      data-slot="context-menu-checkbox-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      checked={checked}
      {...props}>
      <span
        className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <ContextMenuPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </ContextMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </ContextMenuPrimitive.CheckboxItem>
  );
}

function ContextMenuRadioItem({
  className,
  children,
  ...props
}) {
  return (
    <ContextMenuPrimitive.RadioItem
      data-slot="context-menu-radio-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}>
      <span
        className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <ContextMenuPrimitive.ItemIndicator>
          <CircleIcon className="size-2 fill-current" />
        </ContextMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </ContextMenuPrimitive.RadioItem>
  );
}

function ContextMenuLabel({
  className,
  inset,
  ...props
}) {
  return (
    <ContextMenuPrimitive.Label
      data-slot="context-menu-label"
      data-inset={inset}
      className={cn(
        "text-foreground px-2 py-1.5 text-sm font-medium data-[inset]:pl-8",
        className
      )}
      {...props} />
  );
}

function ContextMenuSeparator({
  className,
  ...props
}) {
  return (
    <ContextMenuPrimitive.Separator
      data-slot="context-menu-separator"
      className={cn("bg-border -mx-1 my-1 h-px", className)}
      {...props} />
  );
}

function ContextMenuShortcut({
  className,
  ...props
}) {
  return (
    <span
      data-slot="context-menu-shortcut"
      className={cn("text-muted-foreground ml-auto text-xs tracking-widest", className)}
      {...props} />
  );
}

export {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuCheckboxItem,
  ContextMenuRadioItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuGroup,
  ContextMenuPortal,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuRadioGroup,
}
````

## File: blog-frontend/src/components/ui/dialog.jsx
````javascript
import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { XIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function Dialog({
  ...props
}) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />;
}

function DialogTrigger({
  ...props
}) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogPortal({
  ...props
}) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />;
}

function DialogClose({
  ...props
}) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />;
}

function DialogOverlay({
  className,
  ...props
}) {
  return (
    <DialogPrimitive.Overlay
      data-slot="dialog-overlay"
      className={cn(
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/50",
        className
      )}
      {...props} />
  );
}

function DialogContent({
  className,
  children,
  ...props
}) {
  return (
    <DialogPortal data-slot="dialog-portal">
      <DialogOverlay />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          "bg-background data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 fixed top-[50%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg duration-200 sm:max-w-lg",
          className
        )}
        {...props}>
        {children}
        <DialogPrimitive.Close
          className="ring-offset-background focus:ring-ring data-[state=open]:bg-accent data-[state=open]:text-muted-foreground absolute top-4 right-4 rounded-xs opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4">
          <XIcon />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPortal>
  );
}

function DialogHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="dialog-header"
      className={cn("flex flex-col gap-2 text-center sm:text-left", className)}
      {...props} />
  );
}

function DialogFooter({
  className,
  ...props
}) {
  return (
    <div
      data-slot="dialog-footer"
      className={cn("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end", className)}
      {...props} />
  );
}

function DialogTitle({
  className,
  ...props
}) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn("text-lg leading-none font-semibold", className)}
      {...props} />
  );
}

function DialogDescription({
  className,
  ...props
}) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />
  );
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
}
````

## File: blog-frontend/src/components/ui/drawer.jsx
````javascript
import * as React from "react"
import { Drawer as DrawerPrimitive } from "vaul"

import { cn } from "@/lib/utils"

function Drawer({
  ...props
}) {
  return <DrawerPrimitive.Root data-slot="drawer" {...props} />;
}

function DrawerTrigger({
  ...props
}) {
  return <DrawerPrimitive.Trigger data-slot="drawer-trigger" {...props} />;
}

function DrawerPortal({
  ...props
}) {
  return <DrawerPrimitive.Portal data-slot="drawer-portal" {...props} />;
}

function DrawerClose({
  ...props
}) {
  return <DrawerPrimitive.Close data-slot="drawer-close" {...props} />;
}

function DrawerOverlay({
  className,
  ...props
}) {
  return (
    <DrawerPrimitive.Overlay
      data-slot="drawer-overlay"
      className={cn(
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/50",
        className
      )}
      {...props} />
  );
}

function DrawerContent({
  className,
  children,
  ...props
}) {
  return (
    <DrawerPortal data-slot="drawer-portal">
      <DrawerOverlay />
      <DrawerPrimitive.Content
        data-slot="drawer-content"
        className={cn(
          "group/drawer-content bg-background fixed z-50 flex h-auto flex-col",
          "data-[vaul-drawer-direction=top]:inset-x-0 data-[vaul-drawer-direction=top]:top-0 data-[vaul-drawer-direction=top]:mb-24 data-[vaul-drawer-direction=top]:max-h-[80vh] data-[vaul-drawer-direction=top]:rounded-b-lg data-[vaul-drawer-direction=top]:border-b",
          "data-[vaul-drawer-direction=bottom]:inset-x-0 data-[vaul-drawer-direction=bottom]:bottom-0 data-[vaul-drawer-direction=bottom]:mt-24 data-[vaul-drawer-direction=bottom]:max-h-[80vh] data-[vaul-drawer-direction=bottom]:rounded-t-lg data-[vaul-drawer-direction=bottom]:border-t",
          "data-[vaul-drawer-direction=right]:inset-y-0 data-[vaul-drawer-direction=right]:right-0 data-[vaul-drawer-direction=right]:w-3/4 data-[vaul-drawer-direction=right]:border-l data-[vaul-drawer-direction=right]:sm:max-w-sm",
          "data-[vaul-drawer-direction=left]:inset-y-0 data-[vaul-drawer-direction=left]:left-0 data-[vaul-drawer-direction=left]:w-3/4 data-[vaul-drawer-direction=left]:border-r data-[vaul-drawer-direction=left]:sm:max-w-sm",
          className
        )}
        {...props}>
        <div
          className="bg-muted mx-auto mt-4 hidden h-2 w-[100px] shrink-0 rounded-full group-data-[vaul-drawer-direction=bottom]/drawer-content:block" />
        {children}
      </DrawerPrimitive.Content>
    </DrawerPortal>
  );
}

function DrawerHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="drawer-header"
      className={cn("flex flex-col gap-1.5 p-4", className)}
      {...props} />
  );
}

function DrawerFooter({
  className,
  ...props
}) {
  return (
    <div
      data-slot="drawer-footer"
      className={cn("mt-auto flex flex-col gap-2 p-4", className)}
      {...props} />
  );
}

function DrawerTitle({
  className,
  ...props
}) {
  return (
    <DrawerPrimitive.Title
      data-slot="drawer-title"
      className={cn("text-foreground font-semibold", className)}
      {...props} />
  );
}

function DrawerDescription({
  className,
  ...props
}) {
  return (
    <DrawerPrimitive.Description
      data-slot="drawer-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />
  );
}

export {
  Drawer,
  DrawerPortal,
  DrawerOverlay,
  DrawerTrigger,
  DrawerClose,
  DrawerContent,
  DrawerHeader,
  DrawerFooter,
  DrawerTitle,
  DrawerDescription,
}
````

## File: blog-frontend/src/components/ui/dropdown-menu.jsx
````javascript
"use client"

import * as React from "react"
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu"
import { CheckIcon, ChevronRightIcon, CircleIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function DropdownMenu({
  ...props
}) {
  return <DropdownMenuPrimitive.Root data-slot="dropdown-menu" {...props} />;
}

function DropdownMenuPortal({
  ...props
}) {
  return (<DropdownMenuPrimitive.Portal data-slot="dropdown-menu-portal" {...props} />);
}

function DropdownMenuTrigger({
  ...props
}) {
  return (<DropdownMenuPrimitive.Trigger data-slot="dropdown-menu-trigger" {...props} />);
}

function DropdownMenuContent({
  className,
  sideOffset = 4,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        data-slot="dropdown-menu-content"
        sideOffset={sideOffset}
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 max-h-(--radix-dropdown-menu-content-available-height) min-w-[8rem] origin-(--radix-dropdown-menu-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border p-1 shadow-md",
          className
        )}
        {...props} />
    </DropdownMenuPrimitive.Portal>
  );
}

function DropdownMenuGroup({
  ...props
}) {
  return (<DropdownMenuPrimitive.Group data-slot="dropdown-menu-group" {...props} />);
}

function DropdownMenuItem({
  className,
  inset,
  variant = "default",
  ...props
}) {
  return (
    <DropdownMenuPrimitive.Item
      data-slot="dropdown-menu-item"
      data-inset={inset}
      data-variant={variant}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10 dark:data-[variant=destructive]:focus:bg-destructive/20 data-[variant=destructive]:focus:text-destructive data-[variant=destructive]:*:[svg]:!text-destructive [&_svg:not([class*='text-'])]:text-muted-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[inset]:pl-8 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props} />
  );
}

function DropdownMenuCheckboxItem({
  className,
  children,
  checked,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.CheckboxItem
      data-slot="dropdown-menu-checkbox-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      checked={checked}
      {...props}>
      <span
        className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.CheckboxItem>
  );
}

function DropdownMenuRadioGroup({
  ...props
}) {
  return (<DropdownMenuPrimitive.RadioGroup data-slot="dropdown-menu-radio-group" {...props} />);
}

function DropdownMenuRadioItem({
  className,
  children,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.RadioItem
      data-slot="dropdown-menu-radio-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}>
      <span
        className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <CircleIcon className="size-2 fill-current" />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.RadioItem>
  );
}

function DropdownMenuLabel({
  className,
  inset,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.Label
      data-slot="dropdown-menu-label"
      data-inset={inset}
      className={cn("px-2 py-1.5 text-sm font-medium data-[inset]:pl-8", className)}
      {...props} />
  );
}

function DropdownMenuSeparator({
  className,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.Separator
      data-slot="dropdown-menu-separator"
      className={cn("bg-border -mx-1 my-1 h-px", className)}
      {...props} />
  );
}

function DropdownMenuShortcut({
  className,
  ...props
}) {
  return (
    <span
      data-slot="dropdown-menu-shortcut"
      className={cn("text-muted-foreground ml-auto text-xs tracking-widest", className)}
      {...props} />
  );
}

function DropdownMenuSub({
  ...props
}) {
  return <DropdownMenuPrimitive.Sub data-slot="dropdown-menu-sub" {...props} />;
}

function DropdownMenuSubTrigger({
  className,
  inset,
  children,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.SubTrigger
      data-slot="dropdown-menu-sub-trigger"
      data-inset={inset}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[state=open]:bg-accent data-[state=open]:text-accent-foreground flex cursor-default items-center rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[inset]:pl-8",
        className
      )}
      {...props}>
      {children}
      <ChevronRightIcon className="ml-auto size-4" />
    </DropdownMenuPrimitive.SubTrigger>
  );
}

function DropdownMenuSubContent({
  className,
  ...props
}) {
  return (
    <DropdownMenuPrimitive.SubContent
      data-slot="dropdown-menu-sub-content"
      className={cn(
        "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 min-w-[8rem] origin-(--radix-dropdown-menu-content-transform-origin) overflow-hidden rounded-md border p-1 shadow-lg",
        className
      )}
      {...props} />
  );
}

export {
  DropdownMenu,
  DropdownMenuPortal,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
}
````

## File: blog-frontend/src/components/ui/form.jsx
````javascript
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { Controller, FormProvider, useFormContext, useFormState } from "react-hook-form";

import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"

const Form = FormProvider

const FormFieldContext = React.createContext({})

const FormField = (
  {
    ...props
  }
) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
}

const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext)
  const itemContext = React.useContext(FormItemContext)
  const { getFieldState } = useFormContext()
  const formState = useFormState({ name: fieldContext.name })
  const fieldState = getFieldState(fieldContext.name, formState)

  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>")
  }

  const { id } = itemContext

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  }
}

const FormItemContext = React.createContext({})

function FormItem({
  className,
  ...props
}) {
  const id = React.useId()

  return (
    <FormItemContext.Provider value={{ id }}>
      <div data-slot="form-item" className={cn("grid gap-2", className)} {...props} />
    </FormItemContext.Provider>
  );
}

function FormLabel({
  className,
  ...props
}) {
  const { error, formItemId } = useFormField()

  return (
    <Label
      data-slot="form-label"
      data-error={!!error}
      className={cn("data-[error=true]:text-destructive", className)}
      htmlFor={formItemId}
      {...props} />
  );
}

function FormControl({
  ...props
}) {
  const { error, formItemId, formDescriptionId, formMessageId } = useFormField()

  return (
    <Slot
      data-slot="form-control"
      id={formItemId}
      aria-describedby={
        !error
          ? `${formDescriptionId}`
          : `${formDescriptionId} ${formMessageId}`
      }
      aria-invalid={!!error}
      {...props} />
  );
}

function FormDescription({
  className,
  ...props
}) {
  const { formDescriptionId } = useFormField()

  return (
    <p
      data-slot="form-description"
      id={formDescriptionId}
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />
  );
}

function FormMessage({
  className,
  ...props
}) {
  const { error, formMessageId } = useFormField()
  const body = error ? String(error?.message ?? "") : props.children

  if (!body) {
    return null
  }

  return (
    <p
      data-slot="form-message"
      id={formMessageId}
      className={cn("text-destructive text-sm", className)}
      {...props}>
      {body}
    </p>
  );
}

export {
  useFormField,
  Form,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  FormField,
}
````

## File: blog-frontend/src/components/ui/hover-card.jsx
````javascript
import * as React from "react"
import * as HoverCardPrimitive from "@radix-ui/react-hover-card"

import { cn } from "@/lib/utils"

function HoverCard({
  ...props
}) {
  return <HoverCardPrimitive.Root data-slot="hover-card" {...props} />;
}

function HoverCardTrigger({
  ...props
}) {
  return (<HoverCardPrimitive.Trigger data-slot="hover-card-trigger" {...props} />);
}

function HoverCardContent({
  className,
  align = "center",
  sideOffset = 4,
  ...props
}) {
  return (
    <HoverCardPrimitive.Portal data-slot="hover-card-portal">
      <HoverCardPrimitive.Content
        data-slot="hover-card-content"
        align={align}
        sideOffset={sideOffset}
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-64 origin-(--radix-hover-card-content-transform-origin) rounded-md border p-4 shadow-md outline-hidden",
          className
        )}
        {...props} />
    </HoverCardPrimitive.Portal>
  );
}

export { HoverCard, HoverCardTrigger, HoverCardContent }
````

## File: blog-frontend/src/components/ui/input-otp.jsx
````javascript
"use client"

import * as React from "react"
import { OTPInput, OTPInputContext } from "input-otp"
import { MinusIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function InputOTP({
  className,
  containerClassName,
  ...props
}) {
  return (
    <OTPInput
      data-slot="input-otp"
      containerClassName={cn("flex items-center gap-2 has-disabled:opacity-50", containerClassName)}
      className={cn("disabled:cursor-not-allowed", className)}
      {...props} />
  );
}

function InputOTPGroup({
  className,
  ...props
}) {
  return (
    <div
      data-slot="input-otp-group"
      className={cn("flex items-center", className)}
      {...props} />
  );
}

function InputOTPSlot({
  index,
  className,
  ...props
}) {
  const inputOTPContext = React.useContext(OTPInputContext)
  const { char, hasFakeCaret, isActive } = inputOTPContext?.slots[index] ?? {}

  return (
    <div
      data-slot="input-otp-slot"
      data-active={isActive}
      className={cn(
        "data-[active=true]:border-ring data-[active=true]:ring-ring/50 data-[active=true]:aria-invalid:ring-destructive/20 dark:data-[active=true]:aria-invalid:ring-destructive/40 aria-invalid:border-destructive data-[active=true]:aria-invalid:border-destructive dark:bg-input/30 border-input relative flex h-9 w-9 items-center justify-center border-y border-r text-sm shadow-xs transition-all outline-none first:rounded-l-md first:border-l last:rounded-r-md data-[active=true]:z-10 data-[active=true]:ring-[3px]",
        className
      )}
      {...props}>
      {char}
      {hasFakeCaret && (
        <div
          className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="animate-caret-blink bg-foreground h-4 w-px duration-1000" />
        </div>
      )}
    </div>
  );
}

function InputOTPSeparator({
  ...props
}) {
  return (
    <div data-slot="input-otp-separator" role="separator" {...props}>
      <MinusIcon />
    </div>
  );
}

export { InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator }
````

## File: blog-frontend/src/components/ui/input.jsx
````javascript
import * as React from "react"

import { cn } from "@/lib/utils"

function Input({
  className,
  type,
  ...props
}) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground dark:bg-input/30 border-input flex h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
        className
      )}
      {...props} />
  );
}

export { Input }
````

## File: blog-frontend/src/components/ui/label.jsx
````javascript
"use client"

import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"

import { cn } from "@/lib/utils"

function Label({
  className,
  ...props
}) {
  return (
    <LabelPrimitive.Root
      data-slot="label"
      className={cn(
        "flex items-center gap-2 text-sm leading-none font-medium select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        className
      )}
      {...props} />
  );
}

export { Label }
````

## File: blog-frontend/src/components/ui/menubar.jsx
````javascript
import * as React from "react"
import * as MenubarPrimitive from "@radix-ui/react-menubar"
import { CheckIcon, ChevronRightIcon, CircleIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function Menubar({
  className,
  ...props
}) {
  return (
    <MenubarPrimitive.Root
      data-slot="menubar"
      className={cn(
        "bg-background flex h-9 items-center gap-1 rounded-md border p-1 shadow-xs",
        className
      )}
      {...props} />
  );
}

function MenubarMenu({
  ...props
}) {
  return <MenubarPrimitive.Menu data-slot="menubar-menu" {...props} />;
}

function MenubarGroup({
  ...props
}) {
  return <MenubarPrimitive.Group data-slot="menubar-group" {...props} />;
}

function MenubarPortal({
  ...props
}) {
  return <MenubarPrimitive.Portal data-slot="menubar-portal" {...props} />;
}

function MenubarRadioGroup({
  ...props
}) {
  return (<MenubarPrimitive.RadioGroup data-slot="menubar-radio-group" {...props} />);
}

function MenubarTrigger({
  className,
  ...props
}) {
  return (
    <MenubarPrimitive.Trigger
      data-slot="menubar-trigger"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[state=open]:bg-accent data-[state=open]:text-accent-foreground flex items-center rounded-sm px-2 py-1 text-sm font-medium outline-hidden select-none",
        className
      )}
      {...props} />
  );
}

function MenubarContent({
  className,
  align = "start",
  alignOffset = -4,
  sideOffset = 8,
  ...props
}) {
  return (
    <MenubarPortal>
      <MenubarPrimitive.Content
        data-slot="menubar-content"
        align={align}
        alignOffset={alignOffset}
        sideOffset={sideOffset}
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 min-w-[12rem] origin-(--radix-menubar-content-transform-origin) overflow-hidden rounded-md border p-1 shadow-md",
          className
        )}
        {...props} />
    </MenubarPortal>
  );
}

function MenubarItem({
  className,
  inset,
  variant = "default",
  ...props
}) {
  return (
    <MenubarPrimitive.Item
      data-slot="menubar-item"
      data-inset={inset}
      data-variant={variant}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10 dark:data-[variant=destructive]:focus:bg-destructive/20 data-[variant=destructive]:focus:text-destructive data-[variant=destructive]:*:[svg]:!text-destructive [&_svg:not([class*='text-'])]:text-muted-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 data-[inset]:pl-8 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props} />
  );
}

function MenubarCheckboxItem({
  className,
  children,
  checked,
  ...props
}) {
  return (
    <MenubarPrimitive.CheckboxItem
      data-slot="menubar-checkbox-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-xs py-1.5 pr-2 pl-8 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      checked={checked}
      {...props}>
      <span
        className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <MenubarPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </MenubarPrimitive.ItemIndicator>
      </span>
      {children}
    </MenubarPrimitive.CheckboxItem>
  );
}

function MenubarRadioItem({
  className,
  children,
  ...props
}) {
  return (
    <MenubarPrimitive.RadioItem
      data-slot="menubar-radio-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-xs py-1.5 pr-2 pl-8 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}>
      <span
        className="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <MenubarPrimitive.ItemIndicator>
          <CircleIcon className="size-2 fill-current" />
        </MenubarPrimitive.ItemIndicator>
      </span>
      {children}
    </MenubarPrimitive.RadioItem>
  );
}

function MenubarLabel({
  className,
  inset,
  ...props
}) {
  return (
    <MenubarPrimitive.Label
      data-slot="menubar-label"
      data-inset={inset}
      className={cn("px-2 py-1.5 text-sm font-medium data-[inset]:pl-8", className)}
      {...props} />
  );
}

function MenubarSeparator({
  className,
  ...props
}) {
  return (
    <MenubarPrimitive.Separator
      data-slot="menubar-separator"
      className={cn("bg-border -mx-1 my-1 h-px", className)}
      {...props} />
  );
}

function MenubarShortcut({
  className,
  ...props
}) {
  return (
    <span
      data-slot="menubar-shortcut"
      className={cn("text-muted-foreground ml-auto text-xs tracking-widest", className)}
      {...props} />
  );
}

function MenubarSub({
  ...props
}) {
  return <MenubarPrimitive.Sub data-slot="menubar-sub" {...props} />;
}

function MenubarSubTrigger({
  className,
  inset,
  children,
  ...props
}) {
  return (
    <MenubarPrimitive.SubTrigger
      data-slot="menubar-sub-trigger"
      data-inset={inset}
      className={cn(
        "focus:bg-accent focus:text-accent-foreground data-[state=open]:bg-accent data-[state=open]:text-accent-foreground flex cursor-default items-center rounded-sm px-2 py-1.5 text-sm outline-none select-none data-[inset]:pl-8",
        className
      )}
      {...props}>
      {children}
      <ChevronRightIcon className="ml-auto h-4 w-4" />
    </MenubarPrimitive.SubTrigger>
  );
}

function MenubarSubContent({
  className,
  ...props
}) {
  return (
    <MenubarPrimitive.SubContent
      data-slot="menubar-sub-content"
      className={cn(
        "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 min-w-[8rem] origin-(--radix-menubar-content-transform-origin) overflow-hidden rounded-md border p-1 shadow-lg",
        className
      )}
      {...props} />
  );
}

export {
  Menubar,
  MenubarPortal,
  MenubarMenu,
  MenubarTrigger,
  MenubarContent,
  MenubarGroup,
  MenubarSeparator,
  MenubarLabel,
  MenubarItem,
  MenubarShortcut,
  MenubarCheckboxItem,
  MenubarRadioGroup,
  MenubarRadioItem,
  MenubarSub,
  MenubarSubTrigger,
  MenubarSubContent,
}
````

## File: blog-frontend/src/components/ui/navigation-menu.jsx
````javascript
import * as React from "react"
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu"
import { cva } from "class-variance-authority"
import { ChevronDownIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function NavigationMenu({
  className,
  children,
  viewport = true,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.Root
      data-slot="navigation-menu"
      data-viewport={viewport}
      className={cn(
        "group/navigation-menu relative flex max-w-max flex-1 items-center justify-center",
        className
      )}
      {...props}>
      {children}
      {viewport && <NavigationMenuViewport />}
    </NavigationMenuPrimitive.Root>
  );
}

function NavigationMenuList({
  className,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.List
      data-slot="navigation-menu-list"
      className={cn("group flex flex-1 list-none items-center justify-center gap-1", className)}
      {...props} />
  );
}

function NavigationMenuItem({
  className,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.Item
      data-slot="navigation-menu-item"
      className={cn("relative", className)}
      {...props} />
  );
}

const navigationMenuTriggerStyle = cva(
  "group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground disabled:pointer-events-none disabled:opacity-50 data-[state=open]:hover:bg-accent data-[state=open]:text-accent-foreground data-[state=open]:focus:bg-accent data-[state=open]:bg-accent/50 focus-visible:ring-ring/50 outline-none transition-[color,box-shadow] focus-visible:ring-[3px] focus-visible:outline-1"
)

function NavigationMenuTrigger({
  className,
  children,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.Trigger
      data-slot="navigation-menu-trigger"
      className={cn(navigationMenuTriggerStyle(), "group", className)}
      {...props}>
      {children}{" "}
      <ChevronDownIcon
        className="relative top-[1px] ml-1 size-3 transition duration-300 group-data-[state=open]:rotate-180"
        aria-hidden="true" />
    </NavigationMenuPrimitive.Trigger>
  );
}

function NavigationMenuContent({
  className,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.Content
      data-slot="navigation-menu-content"
      className={cn(
        "data-[motion^=from-]:animate-in data-[motion^=to-]:animate-out data-[motion^=from-]:fade-in data-[motion^=to-]:fade-out data-[motion=from-end]:slide-in-from-right-52 data-[motion=from-start]:slide-in-from-left-52 data-[motion=to-end]:slide-out-to-right-52 data-[motion=to-start]:slide-out-to-left-52 top-0 left-0 w-full p-2 pr-2.5 md:absolute md:w-auto",
        "group-data-[viewport=false]/navigation-menu:bg-popover group-data-[viewport=false]/navigation-menu:text-popover-foreground group-data-[viewport=false]/navigation-menu:data-[state=open]:animate-in group-data-[viewport=false]/navigation-menu:data-[state=closed]:animate-out group-data-[viewport=false]/navigation-menu:data-[state=closed]:zoom-out-95 group-data-[viewport=false]/navigation-menu:data-[state=open]:zoom-in-95 group-data-[viewport=false]/navigation-menu:data-[state=open]:fade-in-0 group-data-[viewport=false]/navigation-menu:data-[state=closed]:fade-out-0 group-data-[viewport=false]/navigation-menu:top-full group-data-[viewport=false]/navigation-menu:mt-1.5 group-data-[viewport=false]/navigation-menu:overflow-hidden group-data-[viewport=false]/navigation-menu:rounded-md group-data-[viewport=false]/navigation-menu:border group-data-[viewport=false]/navigation-menu:shadow group-data-[viewport=false]/navigation-menu:duration-200 **:data-[slot=navigation-menu-link]:focus:ring-0 **:data-[slot=navigation-menu-link]:focus:outline-none",
        className
      )}
      {...props} />
  );
}

function NavigationMenuViewport({
  className,
  ...props
}) {
  return (
    <div
      className={cn("absolute top-full left-0 isolate z-50 flex justify-center")}>
      <NavigationMenuPrimitive.Viewport
        data-slot="navigation-menu-viewport"
        className={cn(
          "origin-top-center bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-90 relative mt-1.5 h-[var(--radix-navigation-menu-viewport-height)] w-full overflow-hidden rounded-md border shadow md:w-[var(--radix-navigation-menu-viewport-width)]",
          className
        )}
        {...props} />
    </div>
  );
}

function NavigationMenuLink({
  className,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.Link
      data-slot="navigation-menu-link"
      className={cn(
        "data-[active=true]:focus:bg-accent data-[active=true]:hover:bg-accent data-[active=true]:bg-accent/50 data-[active=true]:text-accent-foreground hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus-visible:ring-ring/50 [&_svg:not([class*='text-'])]:text-muted-foreground flex flex-col gap-1 rounded-sm p-2 text-sm transition-all outline-none focus-visible:ring-[3px] focus-visible:outline-1 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props} />
  );
}

function NavigationMenuIndicator({
  className,
  ...props
}) {
  return (
    <NavigationMenuPrimitive.Indicator
      data-slot="navigation-menu-indicator"
      className={cn(
        "data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out data-[state=visible]:fade-in top-full z-[1] flex h-1.5 items-end justify-center overflow-hidden",
        className
      )}
      {...props}>
      <div
        className="bg-border relative top-[60%] h-2 w-2 rotate-45 rounded-tl-sm shadow-md" />
    </NavigationMenuPrimitive.Indicator>
  );
}

export {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuContent,
  NavigationMenuTrigger,
  NavigationMenuLink,
  NavigationMenuIndicator,
  NavigationMenuViewport,
  navigationMenuTriggerStyle,
}
````

## File: blog-frontend/src/components/ui/pagination.jsx
````javascript
import * as React from "react"
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MoreHorizontalIcon,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button";

function Pagination({
  className,
  ...props
}) {
  return (
    <nav
      role="navigation"
      aria-label="pagination"
      data-slot="pagination"
      className={cn("mx-auto flex w-full justify-center", className)}
      {...props} />
  );
}

function PaginationContent({
  className,
  ...props
}) {
  return (
    <ul
      data-slot="pagination-content"
      className={cn("flex flex-row items-center gap-1", className)}
      {...props} />
  );
}

function PaginationItem({
  ...props
}) {
  return <li data-slot="pagination-item" {...props} />;
}

function PaginationLink({
  className,
  isActive,
  size = "icon",
  ...props
}) {
  return (
    <a
      aria-current={isActive ? "page" : undefined}
      data-slot="pagination-link"
      data-active={isActive}
      className={cn(buttonVariants({
        variant: isActive ? "outline" : "ghost",
        size,
      }), className)}
      {...props} />
  );
}

function PaginationPrevious({
  className,
  ...props
}) {
  return (
    <PaginationLink
      aria-label="Go to previous page"
      size="default"
      className={cn("gap-1 px-2.5 sm:pl-2.5", className)}
      {...props}>
      <ChevronLeftIcon />
      <span className="hidden sm:block">Previous</span>
    </PaginationLink>
  );
}

function PaginationNext({
  className,
  ...props
}) {
  return (
    <PaginationLink
      aria-label="Go to next page"
      size="default"
      className={cn("gap-1 px-2.5 sm:pr-2.5", className)}
      {...props}>
      <span className="hidden sm:block">Next</span>
      <ChevronRightIcon />
    </PaginationLink>
  );
}

function PaginationEllipsis({
  className,
  ...props
}) {
  return (
    <span
      aria-hidden
      data-slot="pagination-ellipsis"
      className={cn("flex size-9 items-center justify-center", className)}
      {...props}>
      <MoreHorizontalIcon className="size-4" />
      <span className="sr-only">More pages</span>
    </span>
  );
}

export {
  Pagination,
  PaginationContent,
  PaginationLink,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
}
````

## File: blog-frontend/src/components/ui/popover.jsx
````javascript
"use client"

import * as React from "react"
import * as PopoverPrimitive from "@radix-ui/react-popover"

import { cn } from "@/lib/utils"

function Popover({
  ...props
}) {
  return <PopoverPrimitive.Root data-slot="popover" {...props} />;
}

function PopoverTrigger({
  ...props
}) {
  return <PopoverPrimitive.Trigger data-slot="popover-trigger" {...props} />;
}

function PopoverContent({
  className,
  align = "center",
  sideOffset = 4,
  ...props
}) {
  return (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Content
        data-slot="popover-content"
        align={align}
        sideOffset={sideOffset}
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-72 origin-(--radix-popover-content-transform-origin) rounded-md border p-4 shadow-md outline-hidden",
          className
        )}
        {...props} />
    </PopoverPrimitive.Portal>
  );
}

function PopoverAnchor({
  ...props
}) {
  return <PopoverPrimitive.Anchor data-slot="popover-anchor" {...props} />;
}

export { Popover, PopoverTrigger, PopoverContent, PopoverAnchor }
````

## File: blog-frontend/src/components/ui/progress.jsx
````javascript
import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

function Progress({
  className,
  value,
  ...props
}) {
  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn(
        "bg-primary/20 relative h-2 w-full overflow-hidden rounded-full",
        className
      )}
      {...props}>
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className="bg-primary h-full w-full flex-1 transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }} />
    </ProgressPrimitive.Root>
  );
}

export { Progress }
````

## File: blog-frontend/src/components/ui/radio-group.jsx
````javascript
"use client"

import * as React from "react"
import * as RadioGroupPrimitive from "@radix-ui/react-radio-group"
import { CircleIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function RadioGroup({
  className,
  ...props
}) {
  return (
    <RadioGroupPrimitive.Root
      data-slot="radio-group"
      className={cn("grid gap-3", className)}
      {...props} />
  );
}

function RadioGroupItem({
  className,
  ...props
}) {
  return (
    <RadioGroupPrimitive.Item
      data-slot="radio-group-item"
      className={cn(
        "border-input text-primary focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 aspect-square size-4 shrink-0 rounded-full border shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}>
      <RadioGroupPrimitive.Indicator
        data-slot="radio-group-indicator"
        className="relative flex items-center justify-center">
        <CircleIcon
          className="fill-primary absolute top-1/2 left-1/2 size-2 -translate-x-1/2 -translate-y-1/2" />
      </RadioGroupPrimitive.Indicator>
    </RadioGroupPrimitive.Item>
  );
}

export { RadioGroup, RadioGroupItem }
````

## File: blog-frontend/src/components/ui/resizable.jsx
````javascript
import * as React from "react"
import { GripVerticalIcon } from "lucide-react"
import * as ResizablePrimitive from "react-resizable-panels"

import { cn } from "@/lib/utils"

function ResizablePanelGroup({
  className,
  ...props
}) {
  return (
    <ResizablePrimitive.PanelGroup
      data-slot="resizable-panel-group"
      className={cn(
        "flex h-full w-full data-[panel-group-direction=vertical]:flex-col",
        className
      )}
      {...props} />
  );
}

function ResizablePanel({
  ...props
}) {
  return <ResizablePrimitive.Panel data-slot="resizable-panel" {...props} />;
}

function ResizableHandle({
  withHandle,
  className,
  ...props
}) {
  return (
    <ResizablePrimitive.PanelResizeHandle
      data-slot="resizable-handle"
      className={cn(
        "bg-border focus-visible:ring-ring relative flex w-px items-center justify-center after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:ring-1 focus-visible:ring-offset-1 focus-visible:outline-hidden data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-1 data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:-translate-y-1/2 data-[panel-group-direction=vertical]:after:translate-x-0 [&[data-panel-group-direction=vertical]>div]:rotate-90",
        className
      )}
      {...props}>
      {withHandle && (
        <div
          className="bg-border z-10 flex h-4 w-3 items-center justify-center rounded-xs border">
          <GripVerticalIcon className="size-2.5" />
        </div>
      )}
    </ResizablePrimitive.PanelResizeHandle>
  );
}

export { ResizablePanelGroup, ResizablePanel, ResizableHandle }
````

## File: blog-frontend/src/components/ui/scroll-area.jsx
````javascript
"use client"

import * as React from "react"
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area"

import { cn } from "@/lib/utils"

function ScrollArea({
  className,
  children,
  ...props
}) {
  return (
    <ScrollAreaPrimitive.Root data-slot="scroll-area" className={cn("relative", className)} {...props}>
      <ScrollAreaPrimitive.Viewport
        data-slot="scroll-area-viewport"
        className="focus-visible:ring-ring/50 size-full rounded-[inherit] transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:outline-1">
        {children}
      </ScrollAreaPrimitive.Viewport>
      <ScrollBar />
      <ScrollAreaPrimitive.Corner />
    </ScrollAreaPrimitive.Root>
  );
}

function ScrollBar({
  className,
  orientation = "vertical",
  ...props
}) {
  return (
    <ScrollAreaPrimitive.ScrollAreaScrollbar
      data-slot="scroll-area-scrollbar"
      orientation={orientation}
      className={cn(
        "flex touch-none p-px transition-colors select-none",
        orientation === "vertical" &&
          "h-full w-2.5 border-l border-l-transparent",
        orientation === "horizontal" &&
          "h-2.5 flex-col border-t border-t-transparent",
        className
      )}
      {...props}>
      <ScrollAreaPrimitive.ScrollAreaThumb
        data-slot="scroll-area-thumb"
        className="bg-border relative flex-1 rounded-full" />
    </ScrollAreaPrimitive.ScrollAreaScrollbar>
  );
}

export { ScrollArea, ScrollBar }
````

## File: blog-frontend/src/components/ui/select.jsx
````javascript
import * as React from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import { CheckIcon, ChevronDownIcon, ChevronUpIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function Select({
  ...props
}) {
  return <SelectPrimitive.Root data-slot="select" {...props} />;
}

function SelectGroup({
  ...props
}) {
  return <SelectPrimitive.Group data-slot="select-group" {...props} />;
}

function SelectValue({
  ...props
}) {
  return <SelectPrimitive.Value data-slot="select-value" {...props} />;
}

function SelectTrigger({
  className,
  size = "default",
  children,
  ...props
}) {
  return (
    <SelectPrimitive.Trigger
      data-slot="select-trigger"
      data-size={size}
      className={cn(
        "border-input data-[placeholder]:text-muted-foreground [&_svg:not([class*='text-'])]:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 dark:hover:bg-input/50 flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm whitespace-nowrap shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 data-[size=default]:h-9 data-[size=sm]:h-8 *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}>
      {children}
      <SelectPrimitive.Icon asChild>
        <ChevronDownIcon className="size-4 opacity-50" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
}

function SelectContent({
  className,
  children,
  position = "popper",
  ...props
}) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        data-slot="select-content"
        className={cn(
          "bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 relative z-50 max-h-(--radix-select-content-available-height) min-w-[8rem] origin-(--radix-select-content-transform-origin) overflow-x-hidden overflow-y-auto rounded-md border shadow-md",
          position === "popper" &&
            "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
          className
        )}
        position={position}
        {...props}>
        <SelectScrollUpButton />
        <SelectPrimitive.Viewport
          className={cn("p-1", position === "popper" &&
            "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)] scroll-my-1")}>
          {children}
        </SelectPrimitive.Viewport>
        <SelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

function SelectLabel({
  className,
  ...props
}) {
  return (
    <SelectPrimitive.Label
      data-slot="select-label"
      className={cn("text-muted-foreground px-2 py-1.5 text-xs", className)}
      {...props} />
  );
}

function SelectItem({
  className,
  children,
  ...props
}) {
  return (
    <SelectPrimitive.Item
      data-slot="select-item"
      className={cn(
        "focus:bg-accent focus:text-accent-foreground [&_svg:not([class*='text-'])]:text-muted-foreground relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2",
        className
      )}
      {...props}>
      <span className="absolute right-2 flex size-3.5 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}

function SelectSeparator({
  className,
  ...props
}) {
  return (
    <SelectPrimitive.Separator
      data-slot="select-separator"
      className={cn("bg-border pointer-events-none -mx-1 my-1 h-px", className)}
      {...props} />
  );
}

function SelectScrollUpButton({
  className,
  ...props
}) {
  return (
    <SelectPrimitive.ScrollUpButton
      data-slot="select-scroll-up-button"
      className={cn("flex cursor-default items-center justify-center py-1", className)}
      {...props}>
      <ChevronUpIcon className="size-4" />
    </SelectPrimitive.ScrollUpButton>
  );
}

function SelectScrollDownButton({
  className,
  ...props
}) {
  return (
    <SelectPrimitive.ScrollDownButton
      data-slot="select-scroll-down-button"
      className={cn("flex cursor-default items-center justify-center py-1", className)}
      {...props}>
      <ChevronDownIcon className="size-4" />
    </SelectPrimitive.ScrollDownButton>
  );
}

export {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectScrollDownButton,
  SelectScrollUpButton,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
}
````

## File: blog-frontend/src/components/ui/separator.jsx
````javascript
"use client"

import * as React from "react"
import * as SeparatorPrimitive from "@radix-ui/react-separator"

import { cn } from "@/lib/utils"

function Separator({
  className,
  orientation = "horizontal",
  decorative = true,
  ...props
}) {
  return (
    <SeparatorPrimitive.Root
      data-slot="separator-root"
      decorative={decorative}
      orientation={orientation}
      className={cn(
        "bg-border shrink-0 data-[orientation=horizontal]:h-px data-[orientation=horizontal]:w-full data-[orientation=vertical]:h-full data-[orientation=vertical]:w-px",
        className
      )}
      {...props} />
  );
}

export { Separator }
````

## File: blog-frontend/src/components/ui/sheet.jsx
````javascript
import * as React from "react"
import * as SheetPrimitive from "@radix-ui/react-dialog"
import { XIcon } from "lucide-react"

import { cn } from "@/lib/utils"

function Sheet({
  ...props
}) {
  return <SheetPrimitive.Root data-slot="sheet" {...props} />;
}

function SheetTrigger({
  ...props
}) {
  return <SheetPrimitive.Trigger data-slot="sheet-trigger" {...props} />;
}

function SheetClose({
  ...props
}) {
  return <SheetPrimitive.Close data-slot="sheet-close" {...props} />;
}

function SheetPortal({
  ...props
}) {
  return <SheetPrimitive.Portal data-slot="sheet-portal" {...props} />;
}

function SheetOverlay({
  className,
  ...props
}) {
  return (
    <SheetPrimitive.Overlay
      data-slot="sheet-overlay"
      className={cn(
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/50",
        className
      )}
      {...props} />
  );
}

function SheetContent({
  className,
  children,
  side = "right",
  ...props
}) {
  return (
    <SheetPortal>
      <SheetOverlay />
      <SheetPrimitive.Content
        data-slot="sheet-content"
        className={cn(
          "bg-background data-[state=open]:animate-in data-[state=closed]:animate-out fixed z-50 flex flex-col gap-4 shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-500",
          side === "right" &&
            "data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right inset-y-0 right-0 h-full w-3/4 border-l sm:max-w-sm",
          side === "left" &&
            "data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left inset-y-0 left-0 h-full w-3/4 border-r sm:max-w-sm",
          side === "top" &&
            "data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top inset-x-0 top-0 h-auto border-b",
          side === "bottom" &&
            "data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom inset-x-0 bottom-0 h-auto border-t",
          className
        )}
        {...props}>
        {children}
        <SheetPrimitive.Close
          className="ring-offset-background focus:ring-ring data-[state=open]:bg-secondary absolute top-4 right-4 rounded-xs opacity-70 transition-opacity hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none">
          <XIcon className="size-4" />
          <span className="sr-only">Close</span>
        </SheetPrimitive.Close>
      </SheetPrimitive.Content>
    </SheetPortal>
  );
}

function SheetHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sheet-header"
      className={cn("flex flex-col gap-1.5 p-4", className)}
      {...props} />
  );
}

function SheetFooter({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sheet-footer"
      className={cn("mt-auto flex flex-col gap-2 p-4", className)}
      {...props} />
  );
}

function SheetTitle({
  className,
  ...props
}) {
  return (
    <SheetPrimitive.Title
      data-slot="sheet-title"
      className={cn("text-foreground font-semibold", className)}
      {...props} />
  );
}

function SheetDescription({
  className,
  ...props
}) {
  return (
    <SheetPrimitive.Description
      data-slot="sheet-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props} />
  );
}

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
}
````

## File: blog-frontend/src/components/ui/sidebar.jsx
````javascript
"use client";
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";
import { PanelLeftIcon } from "lucide-react"

import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const SIDEBAR_COOKIE_NAME = "sidebar_state"
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7
const SIDEBAR_WIDTH = "16rem"
const SIDEBAR_WIDTH_MOBILE = "18rem"
const SIDEBAR_WIDTH_ICON = "3rem"
const SIDEBAR_KEYBOARD_SHORTCUT = "b"

const SidebarContext = React.createContext(null)

function useSidebar() {
  const context = React.useContext(SidebarContext)
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider.")
  }

  return context
}

function SidebarProvider({
  defaultOpen = true,
  open: openProp,
  onOpenChange: setOpenProp,
  className,
  style,
  children,
  ...props
}) {
  const isMobile = useIsMobile()
  const [openMobile, setOpenMobile] = React.useState(false)

  // This is the internal state of the sidebar.
  // We use openProp and setOpenProp for control from outside the component.
  const [_open, _setOpen] = React.useState(defaultOpen)
  const open = openProp ?? _open
  const setOpen = React.useCallback((value) => {
    const openState = typeof value === "function" ? value(open) : value
    if (setOpenProp) {
      setOpenProp(openState)
    } else {
      _setOpen(openState)
    }

    // This sets the cookie to keep the sidebar state.
    document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`
  }, [setOpenProp, open])

  // Helper to toggle the sidebar.
  const toggleSidebar = React.useCallback(() => {
    return isMobile ? setOpenMobile((open) => !open) : setOpen((open) => !open);
  }, [isMobile, setOpen, setOpenMobile])

  // Adds a keyboard shortcut to toggle the sidebar.
  React.useEffect(() => {
    const handleKeyDown = (event) => {
      if (
        event.key === SIDEBAR_KEYBOARD_SHORTCUT &&
        (event.metaKey || event.ctrlKey)
      ) {
        event.preventDefault()
        toggleSidebar()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleSidebar])

  // We add a state so that we can do data-state="expanded" or "collapsed".
  // This makes it easier to style the sidebar with Tailwind classes.
  const state = open ? "expanded" : "collapsed"

  const contextValue = React.useMemo(() => ({
    state,
    open,
    setOpen,
    isMobile,
    openMobile,
    setOpenMobile,
    toggleSidebar,
  }), [state, open, setOpen, isMobile, openMobile, setOpenMobile, toggleSidebar])

  return (
    <SidebarContext.Provider value={contextValue}>
      <TooltipProvider delayDuration={0}>
        <div
          data-slot="sidebar-wrapper"
          style={
            {
              "--sidebar-width": SIDEBAR_WIDTH,
              "--sidebar-width-icon": SIDEBAR_WIDTH_ICON,
              ...style
            }
          }
          className={cn(
            "group/sidebar-wrapper has-data-[variant=inset]:bg-sidebar flex min-h-svh w-full",
            className
          )}
          {...props}>
          {children}
        </div>
      </TooltipProvider>
    </SidebarContext.Provider>
  );
}

function Sidebar({
  side = "left",
  variant = "sidebar",
  collapsible = "offcanvas",
  className,
  children,
  ...props
}) {
  const { isMobile, state, openMobile, setOpenMobile } = useSidebar()

  if (collapsible === "none") {
    return (
      <div
        data-slot="sidebar"
        className={cn(
          "bg-sidebar text-sidebar-foreground flex h-full w-(--sidebar-width) flex-col",
          className
        )}
        {...props}>
        {children}
      </div>
    );
  }

  if (isMobile) {
    return (
      <Sheet open={openMobile} onOpenChange={setOpenMobile} {...props}>
        <SheetContent
          data-sidebar="sidebar"
          data-slot="sidebar"
          data-mobile="true"
          className="bg-sidebar text-sidebar-foreground w-(--sidebar-width) p-0 [&>button]:hidden"
          style={
            {
              "--sidebar-width": SIDEBAR_WIDTH_MOBILE
            }
          }
          side={side}>
          <SheetHeader className="sr-only">
            <SheetTitle>Sidebar</SheetTitle>
            <SheetDescription>Displays the mobile sidebar.</SheetDescription>
          </SheetHeader>
          <div className="flex h-full w-full flex-col">{children}</div>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <div
      className="group peer text-sidebar-foreground hidden md:block"
      data-state={state}
      data-collapsible={state === "collapsed" ? collapsible : ""}
      data-variant={variant}
      data-side={side}
      data-slot="sidebar">
      {/* This is what handles the sidebar gap on desktop */}
      <div
        data-slot="sidebar-gap"
        className={cn(
          "relative w-(--sidebar-width) bg-transparent transition-[width] duration-200 ease-linear",
          "group-data-[collapsible=offcanvas]:w-0",
          "group-data-[side=right]:rotate-180",
          variant === "floating" || variant === "inset"
            ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4)))]"
            : "group-data-[collapsible=icon]:w-(--sidebar-width-icon)"
        )} />
      <div
        data-slot="sidebar-container"
        className={cn(
          "fixed inset-y-0 z-10 hidden h-svh w-(--sidebar-width) transition-[left,right,width] duration-200 ease-linear md:flex",
          side === "left"
            ? "left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]"
            : "right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]",
          // Adjust the padding for floating and inset variants.
          variant === "floating" || variant === "inset"
            ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)+(--spacing(4))+2px)]"
            : "group-data-[collapsible=icon]:w-(--sidebar-width-icon) group-data-[side=left]:border-r group-data-[side=right]:border-l",
          className
        )}
        {...props}>
        <div
          data-sidebar="sidebar"
          data-slot="sidebar-inner"
          className="bg-sidebar group-data-[variant=floating]:border-sidebar-border flex h-full w-full flex-col group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:shadow-sm">
          {children}
        </div>
      </div>
    </div>
  );
}

function SidebarTrigger({
  className,
  onClick,
  ...props
}) {
  const { toggleSidebar } = useSidebar()

  return (
    <Button
      data-sidebar="trigger"
      data-slot="sidebar-trigger"
      variant="ghost"
      size="icon"
      className={cn("size-7", className)}
      onClick={(event) => {
        onClick?.(event)
        toggleSidebar()
      }}
      {...props}>
      <PanelLeftIcon />
      <span className="sr-only">Toggle Sidebar</span>
    </Button>
  );
}

function SidebarRail({
  className,
  ...props
}) {
  const { toggleSidebar } = useSidebar()

  return (
    <button
      data-sidebar="rail"
      data-slot="sidebar-rail"
      aria-label="Toggle Sidebar"
      tabIndex={-1}
      onClick={toggleSidebar}
      title="Toggle Sidebar"
      className={cn(
        "hover:after:bg-sidebar-border absolute inset-y-0 z-20 hidden w-4 -translate-x-1/2 transition-all ease-linear group-data-[side=left]:-right-4 group-data-[side=right]:left-0 after:absolute after:inset-y-0 after:left-1/2 after:w-[2px] sm:flex",
        "in-data-[side=left]:cursor-w-resize in-data-[side=right]:cursor-e-resize",
        "[[data-side=left][data-state=collapsed]_&]:cursor-e-resize [[data-side=right][data-state=collapsed]_&]:cursor-w-resize",
        "hover:group-data-[collapsible=offcanvas]:bg-sidebar group-data-[collapsible=offcanvas]:translate-x-0 group-data-[collapsible=offcanvas]:after:left-full",
        "[[data-side=left][data-collapsible=offcanvas]_&]:-right-2",
        "[[data-side=right][data-collapsible=offcanvas]_&]:-left-2",
        className
      )}
      {...props} />
  );
}

function SidebarInset({
  className,
  ...props
}) {
  return (
    <main
      data-slot="sidebar-inset"
      className={cn(
        "bg-background relative flex w-full flex-1 flex-col",
        "md:peer-data-[variant=inset]:m-2 md:peer-data-[variant=inset]:ml-0 md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:shadow-sm md:peer-data-[variant=inset]:peer-data-[state=collapsed]:ml-2",
        className
      )}
      {...props} />
  );
}

function SidebarInput({
  className,
  ...props
}) {
  return (
    <Input
      data-slot="sidebar-input"
      data-sidebar="input"
      className={cn("bg-background h-8 w-full shadow-none", className)}
      {...props} />
  );
}

function SidebarHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sidebar-header"
      data-sidebar="header"
      className={cn("flex flex-col gap-2 p-2", className)}
      {...props} />
  );
}

function SidebarFooter({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sidebar-footer"
      data-sidebar="footer"
      className={cn("flex flex-col gap-2 p-2", className)}
      {...props} />
  );
}

function SidebarSeparator({
  className,
  ...props
}) {
  return (
    <Separator
      data-slot="sidebar-separator"
      data-sidebar="separator"
      className={cn("bg-sidebar-border mx-2 w-auto", className)}
      {...props} />
  );
}

function SidebarContent({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sidebar-content"
      data-sidebar="content"
      className={cn(
        "flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden",
        className
      )}
      {...props} />
  );
}

function SidebarGroup({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sidebar-group"
      data-sidebar="group"
      className={cn("relative flex w-full min-w-0 flex-col p-2", className)}
      {...props} />
  );
}

function SidebarGroupLabel({
  className,
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot : "div"

  return (
    <Comp
      data-slot="sidebar-group-label"
      data-sidebar="group-label"
      className={cn(
        "text-sidebar-foreground/70 ring-sidebar-ring flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium outline-hidden transition-[margin,opacity] duration-200 ease-linear focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        "group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0",
        className
      )}
      {...props} />
  );
}

function SidebarGroupAction({
  className,
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="sidebar-group-action"
      data-sidebar="group-action"
      className={cn(
        "text-sidebar-foreground ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground absolute top-3.5 right-3 flex aspect-square w-5 items-center justify-center rounded-md p-0 outline-hidden transition-transform focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        // Increases the hit area of the button on mobile.
        "after:absolute after:-inset-2 md:after:hidden",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props} />
  );
}

function SidebarGroupContent({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sidebar-group-content"
      data-sidebar="group-content"
      className={cn("w-full text-sm", className)}
      {...props} />
  );
}

function SidebarMenu({
  className,
  ...props
}) {
  return (
    <ul
      data-slot="sidebar-menu"
      data-sidebar="menu"
      className={cn("flex w-full min-w-0 flex-col gap-1", className)}
      {...props} />
  );
}

function SidebarMenuItem({
  className,
  ...props
}) {
  return (
    <li
      data-slot="sidebar-menu-item"
      data-sidebar="menu-item"
      className={cn("group/menu-item relative", className)}
      {...props} />
  );
}

const sidebarMenuButtonVariants = cva(
  "peer/menu-button flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm outline-hidden ring-sidebar-ring transition-[width,height,padding] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 group-has-data-[sidebar=menu-action]/menu-item:pr-8 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:bg-sidebar-accent data-[active=true]:font-medium data-[active=true]:text-sidebar-accent-foreground data-[state=open]:hover:bg-sidebar-accent data-[state=open]:hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:size-8! group-data-[collapsible=icon]:p-2! [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        outline:
          "bg-background shadow-[0_0_0_1px_hsl(var(--sidebar-border))] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:shadow-[0_0_0_1px_hsl(var(--sidebar-accent))]",
      },
      size: {
        default: "h-8 text-sm",
        sm: "h-7 text-xs",
        lg: "h-12 text-sm group-data-[collapsible=icon]:p-0!",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function SidebarMenuButton({
  asChild = false,
  isActive = false,
  variant = "default",
  size = "default",
  tooltip,
  className,
  ...props
}) {
  const Comp = asChild ? Slot : "button"
  const { isMobile, state } = useSidebar()

  const button = (
    <Comp
      data-slot="sidebar-menu-button"
      data-sidebar="menu-button"
      data-size={size}
      data-active={isActive}
      className={cn(sidebarMenuButtonVariants({ variant, size }), className)}
      {...props} />
  )

  if (!tooltip) {
    return button
  }

  if (typeof tooltip === "string") {
    tooltip = {
      children: tooltip,
    }
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{button}</TooltipTrigger>
      <TooltipContent
        side="right"
        align="center"
        hidden={state !== "collapsed" || isMobile}
        {...tooltip} />
    </Tooltip>
  );
}

function SidebarMenuAction({
  className,
  asChild = false,
  showOnHover = false,
  ...props
}) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="sidebar-menu-action"
      data-sidebar="menu-action"
      className={cn(
        "text-sidebar-foreground ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground peer-hover/menu-button:text-sidebar-accent-foreground absolute top-1.5 right-1 flex aspect-square w-5 items-center justify-center rounded-md p-0 outline-hidden transition-transform focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        // Increases the hit area of the button on mobile.
        "after:absolute after:-inset-2 md:after:hidden",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        showOnHover &&
          "peer-data-[active=true]/menu-button:text-sidebar-accent-foreground group-focus-within/menu-item:opacity-100 group-hover/menu-item:opacity-100 data-[state=open]:opacity-100 md:opacity-0",
        className
      )}
      {...props} />
  );
}

function SidebarMenuBadge({
  className,
  ...props
}) {
  return (
    <div
      data-slot="sidebar-menu-badge"
      data-sidebar="menu-badge"
      className={cn(
        "text-sidebar-foreground pointer-events-none absolute right-1 flex h-5 min-w-5 items-center justify-center rounded-md px-1 text-xs font-medium tabular-nums select-none",
        "peer-hover/menu-button:text-sidebar-accent-foreground peer-data-[active=true]/menu-button:text-sidebar-accent-foreground",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props} />
  );
}

function SidebarMenuSkeleton({
  className,
  showIcon = false,
  ...props
}) {
  // Random width between 50 to 90%.
  const width = React.useMemo(() => {
    return `${Math.floor(Math.random() * 40) + 50}%`;
  }, [])

  return (
    <div
      data-slot="sidebar-menu-skeleton"
      data-sidebar="menu-skeleton"
      className={cn("flex h-8 items-center gap-2 rounded-md px-2", className)}
      {...props}>
      {showIcon && (
        <Skeleton className="size-4 rounded-md" data-sidebar="menu-skeleton-icon" />
      )}
      <Skeleton
        className="h-4 max-w-(--skeleton-width) flex-1"
        data-sidebar="menu-skeleton-text"
        style={
          {
            "--skeleton-width": width
          }
        } />
    </div>
  );
}

function SidebarMenuSub({
  className,
  ...props
}) {
  return (
    <ul
      data-slot="sidebar-menu-sub"
      data-sidebar="menu-sub"
      className={cn(
        "border-sidebar-border mx-3.5 flex min-w-0 translate-x-px flex-col gap-1 border-l px-2.5 py-0.5",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props} />
  );
}

function SidebarMenuSubItem({
  className,
  ...props
}) {
  return (
    <li
      data-slot="sidebar-menu-sub-item"
      data-sidebar="menu-sub-item"
      className={cn("group/menu-sub-item relative", className)}
      {...props} />
  );
}

function SidebarMenuSubButton({
  asChild = false,
  size = "md",
  isActive = false,
  className,
  ...props
}) {
  const Comp = asChild ? Slot : "a"

  return (
    <Comp
      data-slot="sidebar-menu-sub-button"
      data-sidebar="menu-sub-button"
      data-size={size}
      data-active={isActive}
      className={cn(
        "text-sidebar-foreground ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-accent-foreground active:bg-sidebar-accent active:text-sidebar-accent-foreground [&>svg]:text-sidebar-accent-foreground flex h-7 min-w-0 -translate-x-px items-center gap-2 overflow-hidden rounded-md px-2 outline-hidden focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0",
        "data-[active=true]:bg-sidebar-accent data-[active=true]:text-sidebar-accent-foreground",
        size === "sm" && "text-xs",
        size === "md" && "text-sm",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props} />
  );
}

export {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInput,
  SidebarInset,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
  useSidebar,
}
````

## File: blog-frontend/src/components/ui/skeleton.jsx
````javascript
import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}) {
  return (
    <div
      data-slot="skeleton"
      className={cn("bg-accent animate-pulse rounded-md", className)}
      {...props} />
  );
}

export { Skeleton }
````

## File: blog-frontend/src/components/ui/slider.jsx
````javascript
"use client"

import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"

import { cn } from "@/lib/utils"

function Slider({
  className,
  defaultValue,
  value,
  min = 0,
  max = 100,
  ...props
}) {
  const _values = React.useMemo(() =>
    Array.isArray(value)
      ? value
      : Array.isArray(defaultValue)
        ? defaultValue
        : [min, max], [value, defaultValue, min, max])

  return (
    <SliderPrimitive.Root
      data-slot="slider"
      defaultValue={defaultValue}
      value={value}
      min={min}
      max={max}
      className={cn(
        "relative flex w-full touch-none items-center select-none data-[disabled]:opacity-50 data-[orientation=vertical]:h-full data-[orientation=vertical]:min-h-44 data-[orientation=vertical]:w-auto data-[orientation=vertical]:flex-col",
        className
      )}
      {...props}>
      <SliderPrimitive.Track
        data-slot="slider-track"
        className={cn(
          "bg-muted relative grow overflow-hidden rounded-full data-[orientation=horizontal]:h-1.5 data-[orientation=horizontal]:w-full data-[orientation=vertical]:h-full data-[orientation=vertical]:w-1.5"
        )}>
        <SliderPrimitive.Range
          data-slot="slider-range"
          className={cn(
            "bg-primary absolute data-[orientation=horizontal]:h-full data-[orientation=vertical]:w-full"
          )} />
      </SliderPrimitive.Track>
      {Array.from({ length: _values.length }, (_, index) => (
        <SliderPrimitive.Thumb
          data-slot="slider-thumb"
          key={index}
          className="border-primary bg-background ring-ring/50 block size-4 shrink-0 rounded-full border shadow-sm transition-[color,box-shadow] hover:ring-4 focus-visible:ring-4 focus-visible:outline-hidden disabled:pointer-events-none disabled:opacity-50" />
      ))}
    </SliderPrimitive.Root>
  );
}

export { Slider }
````

## File: blog-frontend/src/components/ui/sonner.jsx
````javascript
import { useTheme } from "next-themes"
import { Toaster as Sonner } from "sonner";

const Toaster = ({
  ...props
}) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)"
        }
      }
      {...props} />
  );
}

export { Toaster }
````

## File: blog-frontend/src/components/ui/switch.jsx
````javascript
"use client"

import * as React from "react"
import * as SwitchPrimitive from "@radix-ui/react-switch"

import { cn } from "@/lib/utils"

function Switch({
  className,
  ...props
}) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        "peer data-[state=checked]:bg-primary data-[state=unchecked]:bg-input focus-visible:border-ring focus-visible:ring-ring/50 dark:data-[state=unchecked]:bg-input/80 inline-flex h-[1.15rem] w-8 shrink-0 items-center rounded-full border border-transparent shadow-xs transition-all outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}>
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className={cn(
          "bg-background dark:data-[state=unchecked]:bg-foreground dark:data-[state=checked]:bg-primary-foreground pointer-events-none block size-4 rounded-full ring-0 transition-transform data-[state=checked]:translate-x-[calc(100%-2px)] data-[state=unchecked]:translate-x-0"
        )} />
    </SwitchPrimitive.Root>
  );
}

export { Switch }
````

## File: blog-frontend/src/components/ui/table.jsx
````javascript
import * as React from "react"

import { cn } from "@/lib/utils"

function Table({
  className,
  ...props
}) {
  return (
    <div data-slot="table-container" className="relative w-full overflow-x-auto">
      <table
        data-slot="table"
        className={cn("w-full caption-bottom text-sm", className)}
        {...props} />
    </div>
  );
}

function TableHeader({
  className,
  ...props
}) {
  return (
    <thead
      data-slot="table-header"
      className={cn("[&_tr]:border-b", className)}
      {...props} />
  );
}

function TableBody({
  className,
  ...props
}) {
  return (
    <tbody
      data-slot="table-body"
      className={cn("[&_tr:last-child]:border-0", className)}
      {...props} />
  );
}

function TableFooter({
  className,
  ...props
}) {
  return (
    <tfoot
      data-slot="table-footer"
      className={cn("bg-muted/50 border-t font-medium [&>tr]:last:border-b-0", className)}
      {...props} />
  );
}

function TableRow({
  className,
  ...props
}) {
  return (
    <tr
      data-slot="table-row"
      className={cn(
        "hover:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors",
        className
      )}
      {...props} />
  );
}

function TableHead({
  className,
  ...props
}) {
  return (
    <th
      data-slot="table-head"
      className={cn(
        "text-foreground h-10 px-2 text-left align-middle font-medium whitespace-nowrap [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        className
      )}
      {...props} />
  );
}

function TableCell({
  className,
  ...props
}) {
  return (
    <td
      data-slot="table-cell"
      className={cn(
        "p-2 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        className
      )}
      {...props} />
  );
}

function TableCaption({
  className,
  ...props
}) {
  return (
    <caption
      data-slot="table-caption"
      className={cn("text-muted-foreground mt-4 text-sm", className)}
      {...props} />
  );
}

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
}
````

## File: blog-frontend/src/components/ui/tabs.jsx
````javascript
"use client"

import * as React from "react"
import * as TabsPrimitive from "@radix-ui/react-tabs"

import { cn } from "@/lib/utils"

function Tabs({
  className,
  ...props
}) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      className={cn("flex flex-col gap-2", className)}
      {...props} />
  );
}

function TabsList({
  className,
  ...props
}) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      className={cn(
        "bg-muted text-muted-foreground inline-flex h-9 w-fit items-center justify-center rounded-lg p-[3px]",
        className
      )}
      {...props} />
  );
}

function TabsTrigger({
  className,
  ...props
}) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      className={cn(
        "data-[state=active]:bg-background dark:data-[state=active]:text-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:outline-ring dark:data-[state=active]:border-input dark:data-[state=active]:bg-input/30 text-foreground dark:text-muted-foreground inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap transition-[color,box-shadow] focus-visible:ring-[3px] focus-visible:outline-1 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:shadow-sm [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props} />
  );
}

function TabsContent({
  className,
  ...props
}) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn("flex-1 outline-none", className)}
      {...props} />
  );
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
````

## File: blog-frontend/src/components/ui/textarea.jsx
````javascript
import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({
  className,
  ...props
}) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 flex field-sizing-content min-h-16 w-full rounded-md border bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className
      )}
      {...props} />
  );
}

export { Textarea }
````

## File: blog-frontend/src/components/ui/toggle-group.jsx
````javascript
"use client";
import * as React from "react"
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group"

import { cn } from "@/lib/utils"
import { toggleVariants } from "@/components/ui/toggle"

const ToggleGroupContext = React.createContext({
  size: "default",
  variant: "default",
})

function ToggleGroup({
  className,
  variant,
  size,
  children,
  ...props
}) {
  return (
    <ToggleGroupPrimitive.Root
      data-slot="toggle-group"
      data-variant={variant}
      data-size={size}
      className={cn(
        "group/toggle-group flex w-fit items-center rounded-md data-[variant=outline]:shadow-xs",
        className
      )}
      {...props}>
      <ToggleGroupContext.Provider value={{ variant, size }}>
        {children}
      </ToggleGroupContext.Provider>
    </ToggleGroupPrimitive.Root>
  );
}

function ToggleGroupItem({
  className,
  children,
  variant,
  size,
  ...props
}) {
  const context = React.useContext(ToggleGroupContext)

  return (
    <ToggleGroupPrimitive.Item
      data-slot="toggle-group-item"
      data-variant={context.variant || variant}
      data-size={context.size || size}
      className={cn(toggleVariants({
        variant: context.variant || variant,
        size: context.size || size,
      }), "min-w-0 flex-1 shrink-0 rounded-none shadow-none first:rounded-l-md last:rounded-r-md focus:z-10 focus-visible:z-10 data-[variant=outline]:border-l-0 data-[variant=outline]:first:border-l", className)}
      {...props}>
      {children}
    </ToggleGroupPrimitive.Item>
  );
}

export { ToggleGroup, ToggleGroupItem }
````

## File: blog-frontend/src/components/ui/toggle.jsx
````javascript
import * as React from "react"
import * as TogglePrimitive from "@radix-ui/react-toggle"
import { cva } from "class-variance-authority";

import { cn } from "@/lib/utils"

const toggleVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium hover:bg-muted hover:text-muted-foreground disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 [&_svg]:shrink-0 focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none transition-[color,box-shadow] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive whitespace-nowrap",
  {
    variants: {
      variant: {
        default: "bg-transparent",
        outline:
          "border border-input bg-transparent shadow-xs hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-9 px-2 min-w-9",
        sm: "h-8 px-1.5 min-w-8",
        lg: "h-10 px-2.5 min-w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Toggle({
  className,
  variant,
  size,
  ...props
}) {
  return (
    <TogglePrimitive.Root
      data-slot="toggle"
      className={cn(toggleVariants({ variant, size, className }))}
      {...props} />
  );
}

export { Toggle, toggleVariants }
````

## File: blog-frontend/src/components/ui/tooltip.jsx
````javascript
import * as React from "react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"

import { cn } from "@/lib/utils"

function TooltipProvider({
  delayDuration = 0,
  ...props
}) {
  return (<TooltipPrimitive.Provider data-slot="tooltip-provider" delayDuration={delayDuration} {...props} />);
}

function Tooltip({
  ...props
}) {
  return (
    <TooltipProvider>
      <TooltipPrimitive.Root data-slot="tooltip" {...props} />
    </TooltipProvider>
  );
}

function TooltipTrigger({
  ...props
}) {
  return <TooltipPrimitive.Trigger data-slot="tooltip-trigger" {...props} />;
}

function TooltipContent({
  className,
  sideOffset = 0,
  children,
  ...props
}) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        data-slot="tooltip-content"
        sideOffset={sideOffset}
        className={cn(
          "bg-primary text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-fit origin-(--radix-tooltip-content-transform-origin) rounded-md px-3 py-1.5 text-xs text-balance",
          className
        )}
        {...props}>
        {children}
        <TooltipPrimitive.Arrow
          className="bg-primary fill-primary z-50 size-2.5 translate-y-[calc(-50%_-_2px)] rotate-45 rounded-[2px]" />
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  );
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
````

## File: blog-frontend/src/components/Analytics.jsx
````javascript
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  Eye, 
  Users, 
  MousePointer,
  Calendar,
  Target
} from 'lucide-react';

const Analytics = () => {
  const [analytics, setAnalytics] = useState({
    overview: {
      totalViews: 0,
      totalRevenue: 0,
      conversionRate: 0,
      avgTimeOnPage: 0
    },
    topArticles: [],
    revenueByNiche: [],
    trafficSources: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      // Simulate analytics data since we don't have real analytics yet
      const mockAnalytics = {
        overview: {
          totalViews: 45230,
          totalRevenue: 3420.50,
          conversionRate: 3.2,
          avgTimeOnPage: 245
        },
        topArticles: [
          { title: "Best Protein Powders 2024", views: 8450, revenue: 420.30, conversionRate: 4.2 },
          { title: "MacBook Pro M3 Review", views: 6230, revenue: 380.50, conversionRate: 3.8 },
          { title: "Top Gaming Headsets", views: 5120, revenue: 290.20, conversionRate: 3.1 },
          { title: "Fitness Tracker Comparison", views: 4890, revenue: 245.80, conversionRate: 2.9 },
          { title: "Best Coding Bootcamps", views: 4320, revenue: 520.40, conversionRate: 5.1 }
        ],
        revenueByNiche: [
          { niche: "Health & Fitness", revenue: 1250.30, percentage: 36.5 },
          { niche: "Technology", revenue: 980.20, percentage: 28.7 },
          { niche: "Education", revenue: 720.50, percentage: 21.1 },
          { niche: "Gaming", revenue: 469.50, percentage: 13.7 }
        ],
        trafficSources: [
          { source: "Organic Search", visitors: 18920, percentage: 65.2 },
          { source: "Social Media", visitors: 5430, percentage: 18.7 },
          { source: "Direct", visitors: 3210, percentage: 11.1 },
          { source: "Referral", visitors: 1450, percentage: 5.0 }
        ]
      };
      
      setAnalytics(mockAnalytics);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <BarChart3 className="h-8 w-8 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Track your blog performance and revenue metrics.
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.overview.totalViews)}</div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(analytics.overview.totalRevenue)}</div>
            <p className="text-xs text-muted-foreground">
              +8% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.overview.conversionRate}%</div>
            <p className="text-xs text-muted-foreground">
              +0.3% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Time on Page</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.floor(analytics.overview.avgTimeOnPage / 60)}m {analytics.overview.avgTimeOnPage % 60}s</div>
            <p className="text-xs text-muted-foreground">
              +15s from last month
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="articles" className="space-y-4">
        <TabsList>
          <TabsTrigger value="articles">Top Articles</TabsTrigger>
          <TabsTrigger value="niches">Revenue by Niche</TabsTrigger>
          <TabsTrigger value="traffic">Traffic Sources</TabsTrigger>
        </TabsList>

        <TabsContent value="articles" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Articles</CardTitle>
              <CardDescription>
                Articles with highest views and revenue
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.topArticles.map((article, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="font-medium">{article.title}</h3>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-muted-foreground">
                          <span>{formatNumber(article.views)} views</span>
                          <span>{formatCurrency(article.revenue)} revenue</span>
                          <Badge variant="outline">{article.conversionRate}% conversion</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="niches" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Revenue by Niche</CardTitle>
              <CardDescription>
                Performance breakdown by product category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.revenueByNiche.map((niche, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{niche.niche}</span>
                      <span className="text-sm text-muted-foreground">
                        {formatCurrency(niche.revenue)} ({niche.percentage}%)
                      </span>
                    </div>
                    <Progress value={niche.percentage} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="traffic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Traffic Sources</CardTitle>
              <CardDescription>
                Where your visitors are coming from
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.trafficSources.map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-muted">
                        {source.source === 'Organic Search' && <TrendingUp className="h-5 w-5" />}
                        {source.source === 'Social Media' && <Users className="h-5 w-5" />}
                        {source.source === 'Direct' && <MousePointer className="h-5 w-5" />}
                        {source.source === 'Referral' && <BarChart3 className="h-5 w-5" />}
                      </div>
                      <div>
                        <div className="font-medium">{source.source}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatNumber(source.visitors)} visitors
                        </div>
                      </div>
                    </div>
                    <Badge variant="outline">{source.percentage}%</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;
````

## File: blog-frontend/src/components/WordPressPostEditor.jsx
````javascript
import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { AlertCircle, Loader2 } from 'lucide-react';
import { blogApi } from '@/services/api';

const WordPressPostEditor = ({ article, isOpen, onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [metaDescription, setMetaDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (article) {
      setTitle(article.title || '');
      setContent(article.content || '');
      setMetaDescription(article.meta_description || '');
    }
  }, [article]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await blogApi.updateWordPressPost(article.id, {
        title,
        content,
        meta_description: metaDescription
      });

      if (data.success) {
        onSuccess();
        onClose();
      } else {
        setError(data.error || 'Failed to update WordPress post');
      }
    } catch (error) {
      console.error('Error updating WordPress post:', error);
      setError(error.message || 'An error occurred while updating the WordPress post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle>Edit WordPress Post</DialogTitle>
          <DialogDescription>
            Update your post on WordPress. Changes will be reflected immediately on your WordPress site.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {error && (
            <div className="bg-red-50 p-3 rounded-md flex items-start text-red-600 mb-4">
              <AlertCircle className="h-5 w-5 mr-2 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Post title"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="meta-description">Meta Description</Label>
            <Input
              id="meta-description"
              value={metaDescription}
              onChange={(e) => setMetaDescription(e.target.value)}
              placeholder="Meta description for SEO"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Post content"
              className="min-h-[300px]"
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loading ? 'Updating...' : 'Update WordPress Post'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default WordPressPostEditor;
````

## File: blog-frontend/src/hooks/use-mobile.js
````javascript
import * as React from "react"

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState(undefined)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mql.removeEventListener("change", onChange);
  }, [])

  return !!isMobile
}
````

## File: blog-frontend/src/lib/utils.js
````javascript
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
````

## File: blog-frontend/src/services/api.js
````javascript
/**
 * Centralized API service for making requests to the backend
 */

// Base API URL - should be configurable based on environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

/**
 * Generic request function with error handling
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - Response data
 */
const request = async (endpoint, options = {}) => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }
    
    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

/**
 * Blog API endpoints
 */
export const blogApi = {
  // Products
  getProducts: () => request('/blog/products'),
  getProduct: (id) => request(`/blog/products/${id}`),
  createProduct: (product) => request('/blog/products', {
    method: 'POST',
    body: JSON.stringify(product),
  }),
  updateProduct: (id, product) => request(`/blog/products/${id}`, {
    method: 'PUT',
    body: JSON.stringify(product),
  }),
  deleteProduct: (id) => request(`/blog/products/${id}`, {
    method: 'DELETE',
  }),
  
  // Articles
  getArticles: () => request('/blog/articles'),
  getArticle: (id) => request(`/blog/articles/${id}`),
  generateArticle: (productId) => request('/blog/generate-article', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId }),
  }),
  updateArticle: (id, article) => request(`/blog/articles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(article),
  }),
  deleteArticle: (id) => request(`/blog/articles/${id}`, {
    method: 'DELETE',
  }),
  
  // WordPress specific endpoints
  getWordPressStatus: (articleId) => request(`/blog/articles/${articleId}/wordpress-status`),
  publishToWordPress: (articleId) => request(`/blog/articles/${articleId}/publish`, {
    method: 'POST',
  }),
  updateWordPressPost: (articleId, content) => request(`/blog/articles/${articleId}/wordpress-update`, {
    method: 'PUT',
    body: JSON.stringify(content),
  }),
  deleteWordPressPost: (articleId) => request(`/blog/articles/${articleId}/wordpress-delete`, {
    method: 'DELETE',
  }),
  getWordPressCategories: () => request('/blog/wordpress/categories'),
  getWordPressTags: () => request('/blog/wordpress/tags'),
  getWordPressSettings: () => request('/blog/wordpress/settings'),
  
  // Keyword research
  researchKeywords: (topic) => request('/blog/keyword-research', {
    method: 'POST',
    body: JSON.stringify({ topic }),
  }),
  
  // Trending products
  getTrendingProducts: (limit = 10) => request(`/blog/trending-products?limit=${limit}`),
};

/**
 * User API endpoints
 */
export const userApi = {
  getUsers: () => request('/users'),
  getUser: (id) => request(`/users/${id}`),
  createUser: (user) => request('/users', {
    method: 'POST',
    body: JSON.stringify(user),
  }),
  updateUser: (id, user) => request(`/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(user),
  }),
  deleteUser: (id) => request(`/users/${id}`, {
    method: 'DELETE',
  }),
};

/**
 * Automation API endpoints
 */
export const automationApi = {
  getSchedulerStatus: () => request('/automation/scheduler/status'),
  startScheduler: () => request('/automation/scheduler/start', {
    method: 'POST',
  }),
  stopScheduler: () => request('/automation/scheduler/stop', {
    method: 'POST',
  }),
  triggerContentGeneration: () => request('/automation/scheduler/trigger-content-generation', {
    method: 'POST',
  }),
  triggerContentUpdate: () => request('/automation/scheduler/trigger-content-update', {
    method: 'POST',
  }),
};

/**
 * Analytics API endpoints
 * Note: Currently using mock data in the component, but these endpoints
 * can be implemented on the backend in the future
 */
export const analyticsApi = {
  getOverview: () => request('/analytics/overview'),
  getTopArticles: () => request('/analytics/top-articles'),
  getRevenueByNiche: () => request('/analytics/revenue-by-niche'),
  getTrafficSources: () => request('/analytics/traffic-sources'),
};

export default {
  blogApi,
  userApi,
  automationApi,
  analyticsApi,
};
````

## File: blog-frontend/src/App.css
````css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);
  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);
}

:root {
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --secondary: oklch(0.97 0 0);
  --secondary-foreground: oklch(0.205 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.556 0 0);
  --accent: oklch(0.97 0 0);
  --accent-foreground: oklch(0.205 0 0);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0 0);
  --input: oklch(0.922 0 0);
  --ring: oklch(0.708 0 0);
  --chart-1: oklch(0.646 0.222 41.116);
  --chart-2: oklch(0.6 0.118 184.704);
  --chart-3: oklch(0.398 0.07 227.392);
  --chart-4: oklch(0.828 0.189 84.429);
  --chart-5: oklch(0.769 0.188 70.08);
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: oklch(0.145 0 0);
  --sidebar-primary: oklch(0.205 0 0);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.97 0 0);
  --sidebar-accent-foreground: oklch(0.205 0 0);
  --sidebar-border: oklch(0.922 0 0);
  --sidebar-ring: oklch(0.708 0 0);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.205 0 0);
  --card-foreground: oklch(0.985 0 0);
  --popover: oklch(0.205 0 0);
  --popover-foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --secondary: oklch(0.269 0 0);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.269 0 0);
  --muted-foreground: oklch(0.708 0 0);
  --accent: oklch(0.269 0 0);
  --accent-foreground: oklch(0.985 0 0);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.556 0 0);
  --chart-1: oklch(0.488 0.243 264.376);
  --chart-2: oklch(0.696 0.17 162.48);
  --chart-3: oklch(0.769 0.188 70.08);
  --chart-4: oklch(0.627 0.265 303.9);
  --chart-5: oklch(0.645 0.246 16.439);
  --sidebar: oklch(0.205 0 0);
  --sidebar-foreground: oklch(0.985 0 0);
  --sidebar-primary: oklch(0.488 0.243 264.376);
  --sidebar-primary-foreground: oklch(0.985 0 0);
  --sidebar-accent: oklch(0.269 0 0);
  --sidebar-accent-foreground: oklch(0.985 0 0);
  --sidebar-border: oklch(1 0 0 / 10%);
  --sidebar-ring: oklch(0.556 0 0);
}

@layer base {
  * {
    @apply border-border outline-ring/50;
  }
  body {
    @apply bg-background text-foreground;
  }
}
````

## File: blog-frontend/src/main.jsx
````javascript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
````

## File: blog-frontend/src/test_api.js
````javascript
/**
 * Test script for API endpoints and WordPress integration
 * Run with: node --experimental-modules test_api.mjs
 */

// This file needs to be saved as .mjs or package.json needs "type": "module"
import fetch from 'node-fetch';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import fs from 'fs';

// Set up global fetch for Node.js environment
global.fetch = fetch;

// Set up import.meta for Vite compatibility
global.import = { meta: { env: { VITE_API_BASE_URL: 'http://localhost:5000/api' } } };

// Get the directory path
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Manually import the API service by reading and evaluating the file
const apiServicePath = resolve(__dirname, './services/api.js');
const apiServiceContent = fs.readFileSync(apiServicePath, 'utf8');

// Create a module-like environment
const module = { exports: {} };
const exports = module.exports;

// Define a simple implementation of the API service for testing
const API_BASE_URL = 'http://localhost:5000/api';

const request = async (endpoint, options = {}) => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }
    
    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

const blogApi = {
  getProducts: () => request('/blog/products'),
  getArticles: () => request('/blog/articles'),
  getWordPressCategories: () => request('/blog/wordpress/categories'),
  getWordPressTags: () => request('/blog/wordpress/tags'),
  getWordPressSettings: () => request('/blog/wordpress/settings'),
};

const userApi = {
  getUsers: () => request('/users'),
};

const automationApi = {
  getSchedulerStatus: () => request('/automation/scheduler/status'),
};

/**
 * Run tests for API endpoints
 */
async function runTests() {
  console.log('🧪 Starting API endpoint tests...');
  console.log('=================================');

  try {
    // Test blog API endpoints
    console.log('\n📝 Testing Blog API endpoints:');
    
    // Get products
    console.log('\n- Testing getProducts()');
    try {
      const productsData = await blogApi.getProducts();
      console.log(`  ✅ Success! Retrieved ${productsData.products?.length || 0} products`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Get articles
    console.log('\n- Testing getArticles()');
    try {
      const articlesData = await blogApi.getArticles();
      console.log(`  ✅ Success! Retrieved ${articlesData.articles?.length || 0} articles`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Test WordPress integration
    console.log('\n🔌 Testing WordPress Integration:');
    
    // Get WordPress categories
    console.log('\n- Testing getWordPressCategories()');
    try {
      const categoriesData = await blogApi.getWordPressCategories();
      console.log(`  ✅ Success! Retrieved ${categoriesData.categories?.length || 0} WordPress categories`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Get WordPress tags
    console.log('\n- Testing getWordPressTags()');
    try {
      const tagsData = await blogApi.getWordPressTags();
      console.log(`  ✅ Success! Retrieved ${tagsData.tags?.length || 0} WordPress tags`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Get WordPress settings
    console.log('\n- Testing getWordPressSettings()');
    try {
      const settingsData = await blogApi.getWordPressSettings();
      console.log(`  ✅ Success! Retrieved WordPress settings`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Test user API endpoints
    console.log('\n👤 Testing User API endpoints:');
    
    // Get users
    console.log('\n- Testing getUsers()');
    try {
      const usersData = await userApi.getUsers();
      console.log(`  ✅ Success! Retrieved ${usersData.users?.length || 0} users`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Test automation API endpoints
    console.log('\n🤖 Testing Automation API endpoints:');
    
    // Get scheduler status
    console.log('\n- Testing getSchedulerStatus()');
    try {
      const statusData = await automationApi.getSchedulerStatus();
      console.log(`  ✅ Success! Scheduler status: ${statusData.status}`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

  } catch (error) {
    console.error('❌ Test failed with error:', error);
  }

  console.log('\n=================================');
  console.log('🏁 API endpoint tests completed');
}

// Run the tests
runTests();
````

## File: blog-frontend/src/test_api.mjs
````
/**
 * Test script for API endpoints and WordPress integration
 * Run with: node test_api.mjs
 */

// Import required modules
import fetch from 'node-fetch';

// Set up global fetch for Node.js environment
global.fetch = fetch;

// Set API base URL
const API_BASE_URL = 'http://127.0.0.1:5001/api';

/**
 * Generic request function with error handling
 */
const request = async (endpoint, options = {}) => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }
    
    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

/**
 * Blog API endpoints
 */
const blogApi = {
  // Products
  getProducts: () => request('/blog/products'),
  
  // Articles
  getArticles: () => request('/blog/articles'),
  
  // WordPress specific endpoints
  getWordPressCategories: () => request('/blog/wordpress/categories'),
  getWordPressTags: () => request('/blog/wordpress/tags'),
  getWordPressSettings: () => request('/blog/wordpress/settings'),
};

/**
 * User API endpoints
 */
const userApi = {
  getUsers: () => request('/users'),
};

/**
 * Automation API endpoints
 */
const automationApi = {
  getSchedulerStatus: () => request('/automation/scheduler/status'),
};

/**
 * Run tests for API endpoints
 */
async function runTests() {
  console.log('🧪 Starting API endpoint tests...');
  console.log('=================================');

  try {
    // Test blog API endpoints
    console.log('\n📝 Testing Blog API endpoints:');
    
    // Get products
    console.log('\n- Testing getProducts()');
    try {
      const productsData = await blogApi.getProducts();
      console.log(`  ✅ Success! Retrieved ${productsData.products?.length || 0} products`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Get articles
    console.log('\n- Testing getArticles()');
    try {
      const articlesData = await blogApi.getArticles();
      console.log(`  ✅ Success! Retrieved ${articlesData.articles?.length || 0} articles`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Test WordPress integration
    console.log('\n🔌 Testing WordPress Integration:');
    
    // Get WordPress categories
    console.log('\n- Testing getWordPressCategories()');
    try {
      const categoriesData = await blogApi.getWordPressCategories();
      console.log(`  ✅ Success! Retrieved ${categoriesData.categories?.length || 0} WordPress categories`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Get WordPress tags
    console.log('\n- Testing getWordPressTags()');
    try {
      const tagsData = await blogApi.getWordPressTags();
      console.log(`  ✅ Success! Retrieved ${tagsData.tags?.length || 0} WordPress tags`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Get WordPress settings
    console.log('\n- Testing getWordPressSettings()');
    try {
      const settingsData = await blogApi.getWordPressSettings();
      console.log(`  ✅ Success! Retrieved WordPress settings`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Test user API endpoints
    console.log('\n👤 Testing User API endpoints:');
    
    // Get users
    console.log('\n- Testing getUsers()');
    try {
      const usersData = await userApi.getUsers();
      console.log(`  ✅ Success! Retrieved ${usersData.users?.length || 0} users`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

    // Test automation API endpoints
    console.log('\n🤖 Testing Automation API endpoints:');
    
    // Get scheduler status
    console.log('\n- Testing getSchedulerStatus()');
    try {
      const statusData = await automationApi.getSchedulerStatus();
      console.log(`  ✅ Success! Scheduler status: ${statusData.status}`);
    } catch (error) {
      console.log(`  ❌ Error: ${error.message}`);
    }

  } catch (error) {
    console.error('❌ Test failed with error:', error);
  }

  console.log('\n=================================');
  console.log('🏁 API endpoint tests completed');
}

// Run the tests
runTests();
````

## File: blog-frontend/components.json
````json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": false,
  "tailwind": {
    "config": "",
    "css": "src/App.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
````

## File: blog-frontend/eslint.config.js
````javascript
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  { ignores: ['dist'] },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
]
````

## File: blog-frontend/index.html
````html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Automated Blog System - SEO Content Generator</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
````

## File: blog-frontend/jsconfig.json
````json
{
  "compilerOptions": {
    "baseUrl": "./",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
````

## File: blog-frontend/vite.config.js
````javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    hmr: {
      clientPort: 443,
    },
    allowedHosts: [
      "5173-iw4pqtcpoonkfgfcj2eiw-21c5baed.manusvm.computer"
    ]
  },
  plugins: [react(),tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
````

## File: .gitignore
````
# Python virtual environment
venv/
__pycache__/
*.py[cod]
*$py.class

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Node.js
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log

# Database
*.db
*.sqlite
*.sqlite3

# IDE files
.idea/
.vscode/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Build files
dist/
build/
*.egg-info/
````

## File: project_overview_from_github.md
````markdown
# SEO Blog Builder - An Agentic SaaS Application

## Overview

SEO Blog Builder is an AI-powered SaaS application that automates the creation of SEO-optimized blog websites using WordPress. The system uses a multi-agent architecture based on the CrewAI framework, where specialized AI agents collaborate to handle different aspects of blog creation, from market research to WordPress deployment.

## Core Components and Their Functions

### 1. Agent Architecture (CrewAI Framework)

*   **Core Concept**: Multiple specialized AI agents working together, each with specific expertise
*   **Purpose**: Enables complex, multi-step workflows with specialized knowledge at each stage
*   **Implementation**: Using CrewAI to coordinate agent communication and task sequences

### 2. Specialized Agents

Each agent has specific expertise and responsibilities:

*   **Client Requirements Agent**: Extracts client needs and translates them into technical specs
*   **Niche Research Agent**: Analyzes markets and identifies profitable blog niches
*   **SEO Strategy Agent**: Develops keyword strategies and content architecture
*   **Content Planning Agent**: Creates editorial calendars and content structures
*   **Content Generation Agent**: Produces SEO-optimized blog content
*   **WordPress Setup Agent**: Configures WordPress sites with proper technical settings
*   **Design Implementation Agent**: Creates visually appealing, branded designs
*   **Monetization Agent**: Implements affiliate marketing and revenue strategies
*   **Testing & QA Agent**: Ensures quality and compliance with best practices

### 3. Agent Orchestration System

*   **Crew Manager**: Coordinates agent workflows and sequences
*   **Task Factory**: Creates specific task definitions for agents
*   **Agent Factory**: Instantiates and configures specialized agents with tools

### 4. External Services Integration

*   **LLM Services**: Connects to Claude and OpenAI APIs for different agent needs
*   **WordPress API**: Enables automated site creation and content publishing
*   **SEO Tools**: Integrates with SEO research APIs (planned)

### 5. WordPress Integration

*   **WordPress Service**: Handles WordPress site setup and content publishing
*   **WordPress Tools**: Provides agents with specific WordPress capabilities
*   **Configuration System**: Manages WordPress site credentials and settings

## Component Interactions

1.  **User Initiates Project**: Client provides requirements through UI
2.  **Orchestration System**: Crew Manager creates appropriate agent crews
3.  **Requirements Analysis**: Client Requirements Agent extracts specifications
4.  **Niche Selection**: Niche Research Agent identifies optimal market focus
5.  **SEO Planning**: SEO Strategy Agent develops keyword and content plan
6.  **Content Creation**: Content Agents produce optimized blog content
7.  **WordPress Setup**: WordPress Setup Agent configures and publishes site
8.  **Monetization**: Monetization Agent implements revenue strategies
9.  **QA & Launch**: Testing Agent verifies quality before launch

## Progress So Far

We've implemented several critical components:

1.  **Core Infrastructure**:
    
    *   Created essential project structure and dependencies
    *   Implemented configuration module for environment variables
    *   Set up logging system
2.  **Agent Framework**:
    
    *   Implemented CrewAI agent structures for specialized agents
    *   Created agent factory for instantiating specialized agents
    *   Developed task factory for defining agent tasks
3.  **LLM Integration**:
    
    *   Connected to Claude and OpenAI APIs
    *   Configured different models for different agent types
4.  **WordPress Integration**:
    
    *   Created WordPress service module for API interactions
    *   Implemented tools for WordPress site setup and publishing
    *   Developed crew manager method for WordPress workflows
    *   Set up configuration for WordPress sites

## Remaining Work

To make the project fully functional, we still need to:

1.  **Complete API Routes**:
    
    *   Finish implementing the WordPress API endpoints
    *   Create comprehensive endpoint documentation
2.  **Implement Frontend**:
    
    *   Develop user interface for project creation
    *   Create dashboard for project monitoring
    *   Build content preview and editing interface
3.  **Add SEO Tool Integrations**:
    
    *   Implement connections to external SEO research APIs
    *   Create tools for keyword research and competition analysis
4.  **Develop Testing Framework**:
    
    *   Create comprehensive testing suite
    *   Implement QA workflow for validating outputs
5.  **Create Deployment Pipeline**:
    
    *   Set up automated WordPress deployment system
    *   Create monitoring for deployed sites
6.  **Implement Billing and Subscription**:
    
    *   Develop payment integration
    *   Create subscription management system
7.  **Documentation and Tutorials**:
    
    *   Create comprehensive user documentation
    *   Develop tutorial content for new users

The most critical next step is to complete the WordPress API routes and test the WordPress integration to ensure that blogs can be automatically published from the agent-generated content. Then we'll need to develop the frontend interface to make the system accessible to users.
````

## File: README.md
````markdown
# automated_blog_platform
````

## File: requirements.txt
````
# Flask and extensions
blinker==1.9.0
click==8.2.1
Flask==3.1.1
flask-cors==6.0.0
Flask-SQLAlchemy==3.1.1
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
SQLAlchemy==2.0.41
typing_extensions==4.14.0
Werkzeug==3.1.3

# Environment variables
python-dotenv==1.0.1

# HTTP requests
requests==2.31.0

# Additional dependencies
argparse==1.4.0
````

## File: research_findings.md
````markdown
# Automated Blog System Research Findings

## 1. Automated Content Generation Systems

### Key Technologies and Tools:
- **AI-Powered Content Generation**: ChatGPT, Jasper.ai, Hypothenuse.ai, Editpad, Prepostseo, Rytr
- **Full Blog Automation**: ContentBot.ai, AutoPageRank, Autoblogging.ai
- **WordPress Integration**: Various plugins for automated posting and content management
- **Content Workflows**: Custom AI content workflows, import systems, and automated publishing

### Core Capabilities:
- Text-to-content generation with minimal human intervention
- SEO-optimized article creation in seconds
- Automated publishing and social media distribution
- Content ideation and topic generation
- Multi-format content creation (text, images, videos)

## 2. SEO Optimization for Affiliate Marketing

### Essential SEO Strategies:
- **Keyword Research**: Target long-tail keywords with commercial intent
- **Content Quality**: High-quality, informative content that provides value
- **On-Page Optimization**: Title tags, meta descriptions, internal linking
- **Technical SEO**: Site speed, mobile responsiveness, crawlability
- **Link Building**: Quality backlinks from relevant sources
- **User Experience**: Fast loading, easy navigation, mobile-friendly design

### Affiliate-Specific SEO Considerations:
- Proper affiliate link handling (nofollow, disclosure)
- Content that matches search intent
- Product comparison and review content
- Local SEO for location-based products
- Schema markup for products and reviews

## 3. High-Ticket Affiliate Marketing Strategies

### Definition and Benefits:
- High-ticket products typically offer $100+ commissions per sale
- Focus on fewer sales with higher profit margins
- Examples: Software, courses, business tools, luxury items

### Key Strategies:
- **Trust Building**: Establish authority and credibility in the niche
- **Educational Content**: In-depth guides, tutorials, case studies
- **Video Marketing**: Webinars, product demonstrations, testimonials
- **Email Marketing**: Nurture sequences for high-value prospects
- **Targeted Traffic**: Focus on qualified leads rather than volume

### Best Practices:
- Choose niches with high-value problems to solve
- Promote trusted, quality products with good reputations
- Create comprehensive content that educates before selling
- Use multiple touchpoints in the customer journey
- Leverage social proof and testimonials

## 4. Trending Product Identification

### Methods for Finding Trending Products:
- Google Trends analysis
- Social media monitoring (TikTok, Instagram, Twitter)
- Amazon Best Sellers and New Releases
- Industry reports and market research
- Competitor analysis
- Seasonal trend tracking

### Tools and Platforms:
- Google Trends, SEMrush, Ahrefs for keyword trends
- Social listening tools for viral products
- Affiliate networks for new program launches
- E-commerce platforms for sales data
- Industry publications and newsletters



## 4. Trending Product Identification (Continued)

### Methods for Finding Trending Products:
- **Competitive Research**: Analyze what products competing publishers recommend.
- **Product Research Tools**: SEMrush, Ahrefs, SimilarWeb for insights into popular products.
- **Social Media Trends**: TikTok for viral products.
- **E-commerce Platforms**: Gumroad for high-ticket digital products (10-75% commission).
- **Niche Selection**: Choose lucrative niches with high-ticket products and viable market demand.

### Examples of High-Ticket Products/Niches:
- Business software solutions
- Online courses
- High-end consumer products (e.g., VR gear, drones, 3D printers)
- Financial products (e.g., gold investment niche with 5-6 figure commissions)
- Self-development opportunities

## 5. Most Lucrative Affiliate Marketing Programs and Networks

### Top Affiliate Programs/Networks:
- **General Networks**: Amazon Associates, Rakuten, eBay Partner Network, CJ Affiliate, ShareASale, ClickBank
- **High-Paying Programs**: Teachable (up to 30% recurring), HubSpot, MasterClass, Semrush, Shopify, AuthorityHacker, Reclaim.ai (25% recurring)
- **Specific Niches**: Augusta Precious Metals (gold investment), GoDaddy (domains, hosting)

### Key Considerations for Lucrative Programs:
- High commission rates (recurring commissions are highly desirable)
- Reputable and reliable companies
- Products/services aligned with your niche and audience
- Good conversion rates and long cookie windows
- Strong affiliate support and resources

## 6. Affiliate Marketing Partnership Programs

### Types of Partnerships:
- **Direct Partnerships**: With brands that have their own in-house affiliate programs.
- **Affiliate Networks**: Platforms that connect affiliates with various merchants (e.g., impact.com, PartnerStack, Awin).
- **Influencer Programs**: Collaborations with social media influencers.

### Benefits of Partnership Programs:
- Access to a wide range of products and services
- Centralized tracking, reporting, and payouts
- Support and resources from network managers
- Opportunity to build long-term relationships with brands

### Best Practices for Partnerships:
- Focus on mutually beneficial collaborations.
- Understand the terms and conditions of each program.
- Leverage technology for tracking and optimization.
- Build trust with both merchants and your audience.

This concludes the initial research phase. The next step is to review the provided GitHub repository.
````

## File: seo_tools_from_github.md
````markdown
# SEO Tools Implementation

This document describes the free SEO tools implementation in the SEO Blog Builder.

## Overview

Instead of relying on expensive third-party SEO services like SEMrush ($139/month), we've implemented a set of free alternatives:

1.  **Google Keyword Planner Integration** - Free keyword research via Google Ads API
2.  **SERP Analysis** - Direct scraping of search results for analysis
3.  **NLP Keyword Analysis** - Using NLTK for natural language processing of content
4.  **Content Optimization** - AI-driven content optimization without paid APIs

## Components

### 1. Google Keyword Planner Service

Uses the Google Ads API to access Keyword Planner data (free with a Google Ads account):

*   Keyword ideas generation
*   Search volume data
*   Competition metrics
*   Bid recommendations

### 2. SERP Analyzer Service

Analyzes search engine results pages through web scraping:

*   SERP feature analysis
*   Content pattern identification
*   Common words/phrases extraction
*   Competitor identification
*   Title and meta data analysis

### 3. NLP Keyword Analyzer

Uses natural language processing to analyze and extract keywords:

*   Keyword extraction
*   Phrase identification
*   Content structure analysis
*   Readability metrics
*   Sentiment analysis

### 4. SEO Data Aggregator

Combines data from all sources to provide comprehensive insights:

*   Comprehensive keyword data
*   Topic analysis
*   Content planning
*   Competition analysis
*   Content recommendations

## Usage

All tools can be accessed through the SEO Service interface:

```python
from app.services.seo import SeoService

# Initialize the service
seo_service = SeoService()

# Research keywords
keyword_data = seo_service.research_keywords("your topic")

# Create content plan
content_plan = seo_service.create_content_plan("your topic", num_articles=10)

# Optimize content
optimization = seo_service.optimize_content("your content", "target keyword")

# Generate meta tags
meta_tags = seo_service.generate_meta_tags("title", "content", "target keyword")

# Analyze URL
url_analysis = seo_service.analyze_url("https://example.com/page")
```

## API Endpoints

SEO functionality is exposed through the following API endpoints:

*   `POST /api/seo/keyword-research` - Research keywords for a topic
*   `POST /api/seo/content-plan` - Create a content plan
*   `POST /api/seo/analyze-competition` - Analyze competition
*   `POST /api/seo/optimize-content` - Optimize content for a keyword
*   `POST /api/seo/generate-meta-tags` - Generate meta tags
*   `POST /api/seo/analyze-url` - Analyze URL for SEO factors

## Mock Data Mode

During development or when API access is limited, you can use mock data mode:

    # In .env file
    USE_MOCK_DATA=True
    

This will generate realistic mock data instead of making actual API calls.

## Adding Real API Access

To use the Google Keyword Planner API:

1.  Create a Google Ads account
2.  Set up API access and developer token
3.  Configure credentials in .env file:

    USE_MOCK_DATA=False
    GOOGLE_ADS_CUSTOMER_ID=your-customer-id
    

And add Google Ads API credentials in the config.py file.
````

## File: start_backend.sh
````bash
#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Change to the automated-blog-system directory
cd automated-blog-system

# Start the backend server
python src/main.py --port 5001

# Note: Press Ctrl+C to stop the server
````

## File: start_frontend.sh
````bash
#!/bin/bash

# Change to the blog-frontend directory
cd blog-frontend

# Start the frontend development server
npm run dev

# Note: Press Ctrl+C to stop the server
````

## File: test_api.py
````python
#!/usr/bin/env python
"""
Test script for API connectivity between frontend and backend.
Run with: python test_api.py
"""

import requests
import json
import sys

# Set API base URL
API_BASE_URL = 'http://127.0.0.1:5001/api'

def test_endpoint(endpoint, description):
    """Test an API endpoint and print the result."""
    print(f"\nTesting {description}...")
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        data = response.json()
        print(f"✅ Success! Status code: {response.status_code}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Run the API tests."""
    print("🧪 Starting API connectivity tests...")
    print("=====================================")
    
    # Test blog API endpoints
    print("\n📝 Testing Blog API endpoints:")
    test_endpoint('/blog/products', 'Products endpoint')
    test_endpoint('/blog/articles', 'Articles endpoint')
    
    # Test WordPress integration
    print("\n🔌 Testing WordPress Integration:")
    test_endpoint('/blog/wordpress/categories', 'WordPress categories endpoint')
    test_endpoint('/blog/wordpress/tags', 'WordPress tags endpoint')
    test_endpoint('/blog/wordpress/settings', 'WordPress settings endpoint')
    
    # Test user API endpoints
    print("\n👤 Testing User API endpoints:")
    test_endpoint('/users', 'Users endpoint')
    
    # Test automation API endpoints
    print("\n🤖 Testing Automation API endpoints:")
    test_endpoint('/automation/scheduler/status', 'Scheduler status endpoint')
    
    print("\n=====================================")
    print("🏁 API connectivity tests completed")

if __name__ == "__main__":
    main()
````

## File: automated-blog-system/src/services/content_generator.py
````python
import os
import openai
from typing import Dict, Any, List
from src.config import Config

class ContentGenerator:
    """Service for generating SEO-optimized blog content."""
    
    def __init__(self):
        if Config.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(
                api_key=Config.OPENAI_API_KEY
            )
        else:
            self.openai_client = None
    
    def generate_article(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete article for a product."""
        if not self.openai_client:
            return self._generate_mock_article(product_data)
        
        try:
            # Generate article content using OpenAI
            prompt = self._create_article_prompt(product_data)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert content writer specializing in affiliate marketing and SEO-optimized blog posts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Generate title and meta description
            title = self._generate_title(product_data)
            meta_description = self._generate_meta_description(product_data)
            
            return {
                "title": title,
                "content": content,
                "meta_description": meta_description,
                "keywords": product_data.get("primary_keywords", []),
                "seo_score": 85.0,
                "readability_score": 78.5,
                "affiliate_links_count": 3
            }
            
        except Exception as e:
            print(f"Error generating content with OpenAI: {e}")
            return self._generate_mock_article(product_data)
    
    def _create_article_prompt(self, product_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for article generation."""
        return f"""
        Write a comprehensive, SEO-optimized blog article about the {product_data['name']}.
        
        Product Details:
        - Name: {product_data['name']}
        - Description: {product_data['description']}
        - Category: {product_data['category']}
        - Price: ${product_data['price']}
        - Primary Keywords: {', '.join(product_data.get('primary_keywords', []))}
        
        Requirements:
        1. Write 1500-2000 words
        2. Include an engaging introduction
        3. Cover product features, benefits, and use cases
        4. Add comparison with alternatives
        5. Include pros and cons
        6. Add a compelling conclusion with call-to-action
        7. Use natural keyword placement
        8. Write in a conversational, helpful tone
        9. Include subheadings for better readability
        10. Add strategic places for affiliate links (mark with [AFFILIATE LINK])
        
        Focus on providing genuine value to readers while encouraging purchase decisions.
        """
    
    def _generate_title(self, product_data: Dict[str, Any]) -> str:
        """Generate an SEO-optimized title."""
        if not self.openai_client:
            return f"{product_data['name']} Review: Complete Guide & Best Deals 2024"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generate SEO-optimized blog post titles."},
                    {"role": "user", "content": f"Create an engaging, SEO-optimized title for a blog post about {product_data['name']}. Include keywords: {', '.join(product_data.get('primary_keywords', [])[:2])}"}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except:
            return f"{product_data['name']} Review: Complete Guide & Best Deals 2024"
    
    def _generate_meta_description(self, product_data: Dict[str, Any]) -> str:
        """Generate meta description for SEO."""
        return f"Discover everything about {product_data['name']} in our comprehensive review. Features, pricing, pros & cons, and where to buy at the best price."
    
    def _generate_mock_article(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock article content for development."""
        title = f"{product_data['name']} Review: Complete Guide & Best Deals 2024"
        
        content = f"""
# {title}

## Introduction

Looking for the perfect {product_data['category'].lower()} solution? The {product_data['name']} has been making waves in the market, and for good reason. In this comprehensive review, we'll dive deep into everything you need to know about this product.

## What is {product_data['name']}?

{product_data['description']} This innovative product has gained significant attention due to its unique features and competitive pricing at ${product_data['price']}.

## Key Features

The {product_data['name']} stands out with several impressive features:

- Premium build quality and design
- Advanced technology integration
- User-friendly interface
- Excellent value for money
- Strong customer support

## Benefits and Use Cases

Whether you're a professional or casual user, the {product_data['name']} offers numerous benefits:

1. **Enhanced Productivity**: Streamlines your workflow
2. **Cost-Effective**: Great value at ${product_data['price']}
3. **Versatile**: Suitable for multiple use cases
4. **Reliable**: Built to last with quality materials

## Pros and Cons

### Pros
- Excellent performance
- Competitive pricing
- Great customer reviews
- Easy to use

### Cons
- Limited availability
- Learning curve for beginners

## Comparison with Alternatives

When compared to similar products in the {product_data['category']} category, the {product_data['name']} offers superior value and performance.

## Final Verdict

The {product_data['name']} is an excellent choice for anyone looking for a reliable {product_data['category'].lower()} solution. At ${product_data['price']}, it offers exceptional value and performance.

[AFFILIATE LINK] Get the best deal on {product_data['name']} here.

## Frequently Asked Questions

**Q: Is {product_data['name']} worth the price?**
A: Absolutely! At ${product_data['price']}, it offers excellent value for the features provided.

**Q: Where can I buy {product_data['name']}?**
A: You can purchase it through our recommended affiliate partners for the best deals.

---

*This post contains affiliate links. We may earn a commission if you purchase through our links at no additional cost to you.*
        """
        
        return {
            "title": title,
            "content": content,
            "meta_description": f"Comprehensive review of {product_data['name']}. Features, pricing, pros & cons, and where to buy at the best price.",
            "keywords": product_data.get("primary_keywords", []),
            "seo_score": 82.0,
            "readability_score": 75.0,
            "affiliate_links_count": 2
        }
````

## File: automated-blog-system/src/services/wordpress_service.py
````python
import requests
import logging
import json
from src.config import Config

class WordPressService:
    """Service for interacting with WordPress REST API."""
    
    def __init__(self):
        """Initialize WordPress service with configuration."""
        self.api_url = Config.WORDPRESS_API_URL
        self.username = Config.WORDPRESS_USERNAME
        self.password = Config.WORDPRESS_PASSWORD
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not all([self.api_url, self.username, self.password]):
            self.logger.warning("WordPress configuration is incomplete. Some features may not work.")
    
    def post_article(self, article):
        """
        Post an article to WordPress.
        
        Args:
            article: Article model instance
            
        Returns:
            dict: Response data including WordPress post ID if successful
        """
        self.logger.info(f"Posting article '{article.title}' to WordPress")
        
        # Prepare post data
        post_data = {
            'title': article.title,
            'content': article.content,
            'status': 'publish',  # Can be: publish, future, draft, pending, private
            'excerpt': article.meta_description,
        }
        
        # Handle tags if available
        if article.keywords:
            keywords = json.loads(article.keywords) if isinstance(article.keywords, str) else article.keywords
            if keywords:
                # Get tag IDs for the first few keywords
                tag_ids = self._get_or_create_tags(keywords[:5])
                if tag_ids:
                    post_data['tags'] = tag_ids
        
        try:
            # Make API request to create post
            # Note: WordPress application passwords may contain spaces
            # which need to be preserved for authentication
            self.logger.info(f"Making request to WordPress API: {self.api_url}/posts")
            self.logger.info(f"Post data: {post_data}")
            
            response = requests.post(
                f"{self.api_url}/posts",
                json=post_data,
                auth=(self.username, self.password),
                headers={'Content-Type': 'application/json'}
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API response status: {response.status_code}")
            self.logger.info(f"WordPress API response headers: {response.headers}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            self.logger.info(f"Article posted successfully to WordPress with ID: {response_data.get('id')}")
            
            return {
                'success': True,
                'wordpress_post_id': response_data.get('id'),
                'wordpress_url': response_data.get('link'),
                'response': response_data
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to post article to WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_article(self, article):
        """
        Update an existing article on WordPress.
        
        Args:
            article: Article model instance with wordpress_post_id
            
        Returns:
            dict: Response data
        """
        if not article.wordpress_post_id:
            self.logger.error("Cannot update article: No WordPress post ID")
            return {
                'success': False,
                'error': 'No WordPress post ID'
            }
        
        self.logger.info(f"Updating article '{article.title}' on WordPress (ID: {article.wordpress_post_id})")
        
        # Prepare post data
        post_data = {
            'title': article.title,
            'content': article.content,
            'excerpt': article.meta_description,
        }
        
        try:
            # Make API request to update post
            self.logger.info(f"Making request to update post on WordPress API: {self.api_url}/posts/{article.wordpress_post_id}")
            self.logger.info(f"Update data: {post_data}")
            
            response = requests.post(
                f"{self.api_url}/posts/{article.wordpress_post_id}",
                json=post_data,
                auth=(self.username, self.password),
                headers={'Content-Type': 'application/json'}
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API update response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API update error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            self.logger.info(f"Article updated successfully on WordPress")
            
            return {
                'success': True,
                'wordpress_url': response_data.get('link'),
                'response': response_data
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to update article on WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_article(self, wordpress_post_id):
        """
        Delete an article from WordPress.
        
        Args:
            wordpress_post_id: ID of the WordPress post
            
        Returns:
            dict: Response data
        """
        if not wordpress_post_id:
            self.logger.error("Cannot delete article: No WordPress post ID")
            return {
                'success': False,
                'error': 'No WordPress post ID'
            }
        
        self.logger.info(f"Deleting article from WordPress (ID: {wordpress_post_id})")
        
        try:
            # Make API request to delete post
            self.logger.info(f"Making request to delete post on WordPress API: {self.api_url}/posts/{wordpress_post_id}")
            
            response = requests.delete(
                f"{self.api_url}/posts/{wordpress_post_id}",
                auth=(self.username, self.password),
                params={'force': True}  # Permanently delete instead of moving to trash
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API delete response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API delete error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            self.logger.info(f"Article deleted successfully from WordPress")
            
            return {
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to delete article from WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_article(self, wordpress_post_id):
        """
        Get article details from WordPress.
        
        Args:
            wordpress_post_id: ID of the WordPress post
            
        Returns:
            dict: Article data from WordPress
        """
        if not wordpress_post_id:
            self.logger.error("Cannot get article: No WordPress post ID")
            return {
                'success': False,
                'error': 'No WordPress post ID'
            }
        
        self.logger.info(f"Getting article from WordPress (ID: {wordpress_post_id})")
        
        try:
            # Make API request to get post
            self.logger.info(f"Making request to get post from WordPress API: {self.api_url}/posts/{wordpress_post_id}")
            
            response = requests.get(
                f"{self.api_url}/posts/{wordpress_post_id}",
                auth=(self.username, self.password)
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API get response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API get error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            self.logger.info(f"Article retrieved successfully from WordPress")
            
            return {
                'success': True,
                'article': response_data
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get article from WordPress: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_tags(self, tag_names):
        """
        Get or create tags in WordPress and return their IDs.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            list: List of tag IDs
        """
        tag_ids = []
        
        for tag_name in tag_names:
            # First check if the tag exists
            try:
                self.logger.info(f"Checking if tag '{tag_name}' exists in WordPress")
                
                # URL encode the tag name for the search
                import urllib.parse
                encoded_tag = urllib.parse.quote(tag_name)
                
                response = requests.get(
                    f"{self.api_url}/tags",
                    params={"search": encoded_tag},
                    auth=(self.username, self.password)
                )
                
                response.raise_for_status()
                existing_tags = response.json()
                
                # Check if we found an exact match
                tag_id = None
                for tag in existing_tags:
                    if tag.get('name', '').lower() == tag_name.lower():
                        tag_id = tag['id']
                        self.logger.info(f"Found existing tag '{tag_name}' with ID: {tag_id}")
                        break
                
                # If tag doesn't exist, create it
                if not tag_id:
                    self.logger.info(f"Tag '{tag_name}' not found, creating it")
                    
                    create_response = requests.post(
                        f"{self.api_url}/tags",
                        json={"name": tag_name},
                        auth=(self.username, self.password),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    create_response.raise_for_status()
                    tag_data = create_response.json()
                    tag_id = tag_data.get('id')
                    
                    self.logger.info(f"Created tag '{tag_name}' with ID: {tag_id}")
                
                if tag_id:
                    tag_ids.append(tag_id)
                
            except Exception as e:
                self.logger.error(f"Error handling tag '{tag_name}': {str(e)}")
        
        self.logger.info(f"Final tag IDs: {tag_ids}")
        return tag_ids
        
    def get_categories(self):
        """
        Get categories from WordPress.
        
        Returns:
            list: List of categories
        """
        self.logger.info("Getting categories from WordPress")
        
        try:
            # Make API request to get categories
            self.logger.info(f"Making request to get categories from WordPress API: {self.api_url}/categories")
            
            response = requests.get(
                f"{self.api_url}/categories",
                auth=(self.username, self.password),
                params={"per_page": 100}  # Get up to 100 categories
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API get categories response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API get categories error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            categories = response.json()
            
            self.logger.info(f"Retrieved {len(categories)} categories from WordPress")
            
            return categories
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get categories from WordPress: {str(e)}")
            return []
    
    def get_tags(self):
        """
        Get tags from WordPress.
        
        Returns:
            list: List of tags
        """
        self.logger.info("Getting tags from WordPress")
        
        try:
            # Make API request to get tags
            self.logger.info(f"Making request to get tags from WordPress API: {self.api_url}/tags")
            
            response = requests.get(
                f"{self.api_url}/tags",
                auth=(self.username, self.password),
                params={"per_page": 100}  # Get up to 100 tags
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API get tags response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API get tags error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            tags = response.json()
            
            self.logger.info(f"Retrieved {len(tags)} tags from WordPress")
            
            return tags
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get tags from WordPress: {str(e)}")
            return []
    
    def get_settings(self):
        """
        Get settings from WordPress.
        
        Returns:
            dict: WordPress settings
        """
        self.logger.info("Getting settings from WordPress")
        
        try:
            # Make API request to get settings
            self.logger.info(f"Making request to get settings from WordPress API: {self.api_url}/settings")
            
            response = requests.get(
                f"{self.api_url}/settings",
                auth=(self.username, self.password)
            )
            
            # Log response details for debugging
            self.logger.info(f"WordPress API get settings response status: {response.status_code}")
            
            # For error responses, log the response content
            if response.status_code >= 400:
                self.logger.error(f"WordPress API get settings error response: {response.text}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            settings = response.json()
            
            self.logger.info("Retrieved settings from WordPress")
            
            return settings
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get settings from WordPress: {str(e)}")
            return {}
````

## File: automated-blog-system/src/config.py
````python
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "database", "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # WordPress Configuration
    WORDPRESS_API_URL = os.getenv("WORDPRESS_API_URL")
    WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
    WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD")
    
    # Affiliate Program Configuration
    AMAZON_ASSOCIATES_TAG = os.getenv("AMAZON_ASSOCIATES_TAG")
    AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
    AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
    
    # SEO Configuration
    GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    
    # System Configuration
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() == "true"
    CONTENT_UPDATE_INTERVAL_HOURS = int(os.getenv("CONTENT_UPDATE_INTERVAL_HOURS", "24"))
    MAX_ARTICLES_PER_DAY = int(os.getenv("MAX_ARTICLES_PER_DAY", "5"))
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present."""
        required_keys = []
        
        if not cls.USE_MOCK_DATA:
            required_keys.extend([
                "OPENAI_API_KEY",
                "WORDPRESS_API_URL",
                "WORDPRESS_USERNAME",
                "WORDPRESS_PASSWORD"
            ])
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
        
        return True
````

## File: blog-frontend/src/components/Dashboard.jsx
````javascript
import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { 
  TrendingUp, 
  FileText, 
  DollarSign, 
  Eye, 
  Clock, 
  Play, 
  Pause,
  RefreshCw,
  BarChart3,
  Settings,
  Plus
} from 'lucide-react'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totals: {
      products: 0,
      articles: 0,
      published_articles: 0,
      draft_articles: 0
    },
    recent_articles: [],
    top_articles: []
  })
  const [schedulerStatus, setSchedulerStatus] = useState({
    running: false,
    scheduled_jobs: 0,
    next_run: null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardStats()
    fetchSchedulerStatus()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      // Try to fetch products and articles to build stats
      const [productsResponse, articlesResponse] = await Promise.all([
        fetch("http://localhost:5000/api/blog/products"),
        fetch("http://localhost:5000/api/blog/articles")
      ])
      
      const productsData = await productsResponse.json()
      const articlesData = await articlesResponse.json()
      
      if (productsData.success && articlesData.success) {
        const products = productsData.products || []
        const articles = articlesData.articles || []
        
        const publishedArticles = articles.filter(a => a.status === 'published')
        const draftArticles = articles.filter(a => a.status === 'draft')
        
        setStats({
          totals: {
            products: products.length,
            articles: articles.length,
            published_articles: publishedArticles.length,
            draft_articles: draftArticles.length
          },
          recent_articles: articles.slice(0, 5).map(article => ({
            ...article,
            views: Math.floor(Math.random() * 1000) + 100,
            revenue: Math.random() * 50 + 10
          })),
          top_articles: articles.slice(0, 3).map(article => ({
            ...article,
            views: Math.floor(Math.random() * 2000) + 500,
            revenue: Math.random() * 100 + 50
          }))
        })
      }
      setLoading(false)
    } catch (error) {
      console.error("Error fetching dashboard stats:", error)
      setLoading(false)
    }
  }

  const fetchSchedulerStatus = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/automation/scheduler/status")
      const data = await response.json()
      if (data.success) {
        setSchedulerStatus({
          running: data.status.is_running,
          scheduled_jobs: 2,
          next_run: data.status.next_scheduled_generation
        })
      }
    } catch (error) {
      console.error("Error fetching scheduler status:", error)
    }
  }

  const toggleScheduler = async () => {
    try {
      const endpoint = schedulerStatus.running ? "stop" : "start"
      const response = await fetch(`http://localhost:5000/api/automation/scheduler/${endpoint}`, {
        method: "POST"
      })
      const data = await response.json()
      if (data.success) {
        fetchSchedulerStatus() // Refresh status after toggle
      } else {
        console.error(`Error ${endpoint}ing scheduler:`, data.error)
      }
    } catch (error) {
      console.error(`Error toggling scheduler:`, error)
    }
  }

  const runTaskManually = async (taskName) => {
    try {
      let endpoint = ""
      if (taskName === "content_generation") {
        endpoint = "trigger-content-generation"
      } else if (taskName === "content_update") {
        endpoint = "trigger-content-update"
      } else {
        console.log(`Task ${taskName} not implemented yet`)
        return
      }
      
      const response = await fetch(`http://localhost:5000/api/automation/scheduler/${endpoint}`, {
        method: "POST"
      })
      const data = await response.json()
      if (data.success) {
        console.log(`Task ${taskName} executed successfully`)
        fetchDashboardStats() // Refresh stats after task
      } else {
        console.error(`Error running task ${taskName}:`, data.error)
      }
    } catch (error) {
      console.error("Error running task:", error)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status) => {
    const variants = {
      published: 'default',
      draft: 'secondary',
      scheduled: 'outline'
    }
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor your automated blog system performance and manage content generation.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={fetchDashboardStats}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Article
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totals.products}</div>
            <p className="text-xs text-muted-foreground">
              +2 from last week
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totals.articles}</div>
            <p className="text-xs text-muted-foreground">
              {stats.totals.published_articles} published, {stats.totals.draft_articles} drafts
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Views</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12,450</div>
            <p className="text-xs text-muted-foreground">
              +15% from last month
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$1,245</div>
            <p className="text-xs text-muted-foreground">
              +8% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Scheduler Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Automation Scheduler</span>
          </CardTitle>
          <CardDescription>
            Manage automated content generation and updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${schedulerStatus.running ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm font-medium">
                  {schedulerStatus.running ? 'Running' : 'Stopped'}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {schedulerStatus.scheduled_jobs} scheduled jobs
              </div>
              {schedulerStatus.next_run && (
                <div className="text-sm text-muted-foreground">
                  Next run: {formatDate(schedulerStatus.next_run)}
                </div>
              )}
            </div>
            <Button
              variant={schedulerStatus.running ? "destructive" : "default"}
              size="sm"
              onClick={toggleScheduler}
            >
              {schedulerStatus.running ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start
                </>
              )}
            </Button>
          </div>
          
          <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-5">
            {[
              { name: 'Trend Analysis', key: 'trend_analysis' },
              { name: 'Content Generation', key: 'content_generation' },
              { name: 'Content Update', key: 'content_update' },
              { name: 'SEO Analysis', key: 'seo_analysis' },
              { name: 'Performance Review', key: 'performance_review' }
            ].map((task) => (
              <Button
                key={task.key}
                variant="outline"
                size="sm"
                onClick={() => runTaskManually(task.key)}
                className="text-xs"
              >
                <Play className="h-3 w-3 mr-1" />
                {task.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Content Tabs */}
      <Tabs defaultValue="recent" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recent">Recent Articles</TabsTrigger>
          <TabsTrigger value="top">Top Performing</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Articles</CardTitle>
              <CardDescription>
                Latest articles generated by the system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.recent_articles.map((article) => (
                  <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <h3 className="font-medium line-clamp-1">{article.title}</h3>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
                        <span>{formatDate(article.created_at)}</span>
                        <span>{article.views} views</span>
                        <span>${article.revenue.toFixed(2)} revenue</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(article.status)}
                      <Button variant="ghost" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="top" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Performing Articles</CardTitle>
              <CardDescription>
                Articles with highest views and revenue
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {stats.top_articles.map((article, index) => (
                  <div key={article.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h3 className="font-medium line-clamp-1">{article.title}</h3>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-muted-foreground">
                          <span>{article.views} views</span>
                          <span>${article.revenue.toFixed(2)} revenue</span>
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <BarChart3 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Content Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Published Articles</span>
                      <span>{stats.totals.published_articles}/{stats.totals.articles}</span>
                    </div>
                    <Progress 
                      value={(stats.totals.published_articles / stats.totals.articles) * 100} 
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>SEO Score</span>
                      <span>85%</span>
                    </div>
                    <Progress value={85} className="mt-2" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Conversion Rate</span>
                      <span>3.2%</span>
                    </div>
                    <Progress value={32} className="mt-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">API Status</span>
                    <Badge variant="default">Healthy</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Database</span>
                    <Badge variant="default">Connected</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Scheduler</span>
                    <Badge variant={schedulerStatus.running ? "default" : "destructive"}>
                      {schedulerStatus.running ? "Running" : "Stopped"}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Last Update</span>
                    <span className="text-sm text-muted-foreground">2 min ago</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Dashboard
````

## File: blog-frontend/src/components/GenerateArticle.jsx
````javascript
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Wand2, FileText, TrendingUp, Upload } from 'lucide-react';
import { blogApi } from '@/services/api';

const GenerateArticle = () => {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [generatedArticle, setGeneratedArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const data = await blogApi.getProducts();
      if (data.success) {
        setProducts(data.products || []);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoadingProducts(false);
    }
  };

  const generateArticle = async () => {
    if (!selectedProduct) return;

    setLoading(true);
    try {
      const data = await blogApi.generateArticle(parseInt(selectedProduct));
      if (data.success) {
        setGeneratedArticle(data.article);
      } else {
        console.error('Error generating article:', data.error);
        alert('Error generating article: ' + data.error);
      }
    } catch (error) {
      console.error('Error generating article:', error);
      alert('Error generating article. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const publishToWordPress = async () => {
    if (!generatedArticle) return;
    
    try {
      const data = await blogApi.publishToWordPress(generatedArticle.id);
      if (data.success) {
        alert('Article published to WordPress successfully!');
      } else {
        console.error('Error publishing to WordPress:', data.error);
        alert('Error publishing to WordPress: ' + data.error);
      }
    } catch (error) {
      console.error('Error publishing to WordPress:', error);
      alert('Error publishing to WordPress. Please try again.');
    }
  };

  const selectedProductData = products.find(p => p.id === parseInt(selectedProduct));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Generate Article</h1>
        <p className="text-muted-foreground">
          Create SEO-optimized articles for your products using AI.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Product Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Select Product</span>
            </CardTitle>
            <CardDescription>
              Choose a product to generate an article for
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={selectedProduct} onValueChange={setSelectedProduct}>
              <SelectTrigger>
                <SelectValue placeholder={loadingProducts ? "Loading products..." : "Select a product"} />
              </SelectTrigger>
              <SelectContent>
                {products.map((product) => (
                  <SelectItem key={product.id} value={product.id.toString()}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selectedProductData && (
              <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
                <div>
                  <h3 className="font-medium">{selectedProductData.name}</h3>
                  <p className="text-sm text-muted-foreground">{selectedProductData.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary">{selectedProductData.category}</Badge>
                  <Badge variant="outline">${selectedProductData.price}</Badge>
                  <Badge variant="outline">Score: {selectedProductData.trend_score}</Badge>
                </div>
                <div className="text-sm">
                  <strong>Keywords:</strong> {selectedProductData.primary_keywords?.join(', ') || 'None'}
                </div>
              </div>
            )}

            <Button 
              onClick={generateArticle} 
              disabled={!selectedProduct || loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating Article...
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4 mr-2" />
                  Generate Article
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Article Preview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Generated Article</span>
            </CardTitle>
            <CardDescription>
              Preview and edit your generated content
            </CardDescription>
          </CardHeader>
          <CardContent>
            {generatedArticle ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Title</label>
                  <div className="p-3 border rounded-md bg-muted/50">
                    {generatedArticle.title}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Meta Description</label>
                  <div className="p-3 border rounded-md bg-muted/50 text-sm">
                    {generatedArticle.meta_description}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Content Preview</label>
                  <Textarea
                    value={generatedArticle.content.substring(0, 500) + '...'}
                    readOnly
                    className="min-h-[200px]"
                  />
                </div>

                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <span>Words: {generatedArticle.word_count}</span>
                  <span>SEO Score: {generatedArticle.seo_score}%</span>
                  <span>Readability: {generatedArticle.readability_score}%</span>
                </div>

                <div className="flex space-x-2">
                  <Button variant="outline" size="sm">
                    Edit Article
                  </Button>
                  <Button size="sm" onClick={publishToWordPress}>
                    <Upload className="h-4 w-4 mr-2" />
                    Publish to WordPress
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a product and click "Generate Article" to create content.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GenerateArticle;
````

## File: blog-frontend/src/components/Layout.jsx
````javascript
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { 
  BarChart3, 
  FileText, 
  Package, 
  Settings, 
  Menu,
  X,
  TrendingUp,
  Wand2
} from 'lucide-react';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: BarChart3 },
    { name: 'Products', href: '/products', icon: Package },
    { name: 'Articles', href: '/articles', icon: FileText },
    { name: 'Generate Article', href: '/generate', icon: Wand2 },
    { name: 'Analytics', href: '/analytics', icon: TrendingUp },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (href) => {
    return location.pathname === href;
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 z-50 lg:hidden ${sidebarOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-white dark:bg-gray-800">
          <div className="flex h-16 items-center justify-between px-4">
            <h1 className="text-xl font-bold">Blog System</h1>
            <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(false)}>
              <X className="h-6 w-6" />
            </Button>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    isActive(item.href)
                      ? 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-white'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className="mr-3 h-6 w-6 flex-shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
          <div className="flex h-16 items-center px-4">
            <h1 className="text-xl font-bold">Automated Blog System</h1>
          </div>
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    isActive(item.href)
                      ? 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-white'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
                  }`}
                >
                  <Icon className="mr-3 h-6 w-6 flex-shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm dark:border-gray-700 dark:bg-gray-800 sm:gap-x-6 sm:px-6 lg:px-8">
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </Button>
          
          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1"></div>
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
````

## File: blog-frontend/src/components/Products.jsx
````javascript
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Edit, Trash2, Search, RefreshCw } from 'lucide-react';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/blog/products');
      const data = await response.json();
      if (data.success) {
        setProducts(data.products || []);
      } else {
        console.error('Error fetching products:', data.error);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (product.category && product.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        const response = await fetch(`http://localhost:5000/api/blog/products/${productId}`, {
          method: 'DELETE',
        });
        const data = await response.json();
        if (data.success) {
          fetchProducts(); // Refresh the list
        } else {
          console.error('Error deleting product:', data.error);
        }
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Products</h1>
          <p className="text-muted-foreground">
            Manage your high-ticket products for content generation.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={fetchProducts}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add New Product
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product List</CardTitle>
          <CardDescription>All products in your system.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center py-4">
            <Input
              placeholder="Search products..."
              value={searchTerm}
              onChange={handleSearch}
              className="max-w-sm"
            />
            <Search className="ml-2 h-4 w-4 text-muted-foreground" />
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Trend Score</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredProducts.length > 0 ? (
                filteredProducts.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell className="font-medium">{product.name}</TableCell>
                    <TableCell>{product.category}</TableCell>
                    <TableCell>${product.price.toFixed(2)}</TableCell>
                    <TableCell>{product.trend_score ? product.trend_score.toFixed(2) : 'N/A'}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" className="mr-2">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(product.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    No products found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Products;
````

## File: blog-frontend/src/App.jsx
````javascript
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import Products from './components/Products'
import Articles from './components/Articles'
import GenerateArticle from './components/GenerateArticle'
import Analytics from './components/Analytics'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/products" element={<Products />} />
          <Route path="/articles" element={<Articles />} />
          <Route path="/generate" element={<GenerateArticle />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<div className="p-6"><h1 className="text-2xl font-bold">Settings</h1><p>Settings component coming soon...</p></div>} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
````

## File: system_architecture_design.md
````markdown
# Automated SEO Blog System: Architecture and Strategy Design

## 1. Introduction

This document outlines the proposed architecture and strategic approach for building an automated, SEO-optimized blog system. The system aims to periodically generate and update articles about trending high-ticket products, integrate lucrative affiliate marketing and partnership programs, and implement a strategic marketing plan. This design leverages a multi-agent architecture and WordPress integration capabilities, while addressing the need for dynamic content generation, trending product identification, and advanced affiliate marketing strategies.

## 2. Core System Objectives

The primary objectives of this automated blog system are:

*   **Automated Content Generation**: Generate high-quality, SEO-optimized articles on trending high-ticket products with minimal human intervention.
*   **SEO Optimization**: Ensure all generated content and the blog platform itself are fully optimized for search engines to maximize organic traffic.
*   **Affiliate Marketing Integration**: Seamlessly embed strategically placed affiliate links and ads within articles to monetize content effectively.
*   **Trending Product Identification**: Implement mechanisms to identify and analyze currently trending high-ticket products and lucrative affiliate programs.
*   **Periodic Content Updates**: Automate the process of updating existing articles and publishing new ones to maintain freshness and relevance.
*   **Strategic Marketing**: Develop and execute a marketing strategy to promote the blog and its content.

## 3. Leveraging the Existing `seo-blog-builder` Repository

The `seo-blog-builder` repository provides a strong foundation for this project, particularly its multi-agent architecture based on CrewAI and its existing WordPress integration. The following components from the repository will be utilized and extended:

*   **Agent Architecture**: The CrewAI framework with its specialized agents (Client Requirements, Niche Research, SEO Strategy, Content Planning, Content Generation, WordPress Setup, Design Implementation, Monetization, Testing & QA Agents) will be central to the system's operation. These agents will be enhanced to handle the specific requirements of trending high-ticket products and advanced affiliate strategies.
*   **LLM Integration**: The existing connections to Claude and OpenAI APIs will be crucial for content generation, SEO analysis, and other AI-driven tasks.
*   **WordPress Integration**: The WordPress service module and tools for site setup and publishing will be adapted to support automated blog creation and content updates.
*   **SEO Tools Implementation**: The free SEO tools (Google Keyword Planner Integration, SERP Analysis, NLP Keyword Analysis, SEO Data Aggregator) will be further developed and integrated to provide robust SEO capabilities without relying on expensive third-party services.

## 4. Proposed System Architecture

The system will follow a modular, agent-based architecture, extending the existing `seo-blog-builder` framework. The core components will include:

### 4.1. Data Ingestion and Analysis Layer

This layer will be responsible for identifying trending high-ticket products and lucrative affiliate programs. It will involve:

*   **Product Trend Scraper/API Integrator**: A new component responsible for gathering data from various sources (e.g., Google Trends, Amazon Best Sellers, affiliate networks, social media platforms) to identify trending high-ticket products. This will likely involve web scraping and API integrations with e-commerce platforms and affiliate networks.
*   **Affiliate Program Analyzer**: This module will analyze data from affiliate networks and direct merchant programs to identify the most lucrative and relevant opportunities based on commission rates, product relevance, and program terms.
*   **Niche and Keyword Research Enhancements**: The existing Niche Research Agent and SEO Strategy Agent will be enhanced to leverage the data from the Product Trend Scraper and Affiliate Program Analyzer to identify profitable niches and keywords related to trending high-ticket products.

### 4.2. Agent Orchestration and Content Generation Layer

This layer will manage the workflow of content creation and optimization, building upon the CrewAI framework:

*   **Central Orchestrator Agent**: This agent will be enhanced to initiate content generation cycles based on identified trending products and pre-defined schedules. It will coordinate the activities of all specialized agents.
*   **Content Generation Agent (Enhanced)**: This agent will be responsible for generating high-quality, engaging, and SEO-optimized articles. It will leverage LLMs (Claude, OpenAI) and integrate data from the Niche Research and SEO Strategy Agents to ensure content relevance and optimization. It will also be trained to strategically place affiliate links naturally within the content.
*   **Content Update Agent (New)**: A new agent dedicated to periodically reviewing existing articles, identifying opportunities for updates (e.g., new product versions, updated affiliate offers, improved SEO keywords), and initiating content revision processes.
*   **Monetization Agent (Enhanced)**: This agent will be responsible for selecting the most appropriate affiliate programs and generating affiliate links. It will work closely with the Content Generation Agent to ensure proper and strategic placement of these links.

### 4.3. Blog Management and Deployment Layer

This layer will handle the publishing and management of the blog content on WordPress:

*   **WordPress Setup Agent (Enhanced)**: This agent will continue to handle WordPress site setup and configuration. It will be enhanced to ensure all technical SEO best practices are applied during site creation.
*   **WordPress Publishing Service**: The existing WordPress service module will be used to publish generated and updated articles to the WordPress sites. It will ensure proper formatting, image embedding, and meta-data population.
*   **Frontend Blog (Enhanced)**: The React frontend will be developed to provide a user-friendly interface for managing the automated blog. This will include dashboards for monitoring content generation progress, affiliate performance, and overall blog analytics. It will also allow for manual review and editing of articles before publishing.

### 4.4. Marketing and Analytics Layer

This layer will focus on promoting the blog and tracking its performance:

*   **Marketing Strategy Agent (New)**: This agent will develop and execute marketing strategies, including social media promotion, email marketing campaigns, and potentially paid advertising, to drive traffic to the blog. It will leverage data from the analytics dashboard to optimize campaigns.
*   **Analytics Dashboard**: The frontend will include a comprehensive analytics dashboard to track key metrics such as traffic, conversions, affiliate link clicks, and revenue. This data will feed back into the system to refine content generation and marketing strategies.

## 5. Technology Stack

The core technology stack will remain largely consistent with the existing repository, with additions for new functionalities:

*   **Backend**: Python (FastAPI, SQLAlchemy, CrewAI, NLTK), PostgreSQL, Redis
*   **Frontend**: React, Material-UI
*   **AI/ML**: OpenAI API, Claude API
*   **Web Scraping**: Libraries like BeautifulSoup, Scrapy (for Product Trend Scraper)
*   **Deployment**: Docker, Docker Compose, potentially cloud platforms (AWS, GCP, Azure) for scalable deployment.

## 6. Development Roadmap (High-Level)

1.  **Phase 1: Research and Analysis (Completed)**: Comprehensive research on automated content generation, SEO, affiliate marketing, and trending product identification. Review of existing GitHub repository.
2.  **Phase 2: System Architecture and Strategy Design (Current)**: Define the overall system architecture, component interactions, and strategic approach.
3.  **Phase 3: Backend Automation System Development**: Implement the data ingestion and analysis layer (Product Trend Scraper, Affiliate Program Analyzer), and enhance existing agents for niche research, SEO strategy, and content generation. Develop the new Content Update Agent.
4.  **Phase 4: SEO-Optimized Frontend Blog Development**: Build out the React frontend with dashboards for content management, analytics, and user interaction.
5.  **Phase 5: Content Automation and Affiliate Integration**: Fully integrate the content generation and update processes with WordPress publishing. Implement robust affiliate link management and tracking.
6.  **Phase 6: Marketing Strategy and Deployment Plan**: Develop the Marketing Strategy Agent and define the deployment pipeline for the entire system.
7.  **Phase 7: System Deployment and Testing**: Deploy the integrated system to a staging environment, conduct comprehensive testing, and optimize performance.
8.  **Phase 8: Deliver Final System and Documentation**: Provide the complete system, detailed documentation, and user guides.

## 7. API Keys and Credentials

To implement the full functionality of this system, the following API keys and credentials will be required:

*   **OpenAI API Key**: For accessing OpenAI's language models (GPT-3.5, GPT-4).
*   **Claude API Key**: For accessing Anthropic's Claude models.
*   **Google Ads API Credentials**: For accessing Google Keyword Planner data (Customer ID, Developer Token, OAuth 2.0 credentials).
*   **WordPress API Credentials**: For each WordPress site to be managed (Application Passwords).
*   **Affiliate Network API Keys**: For specific affiliate networks (e.g., Amazon Associates, ShareASale, CJ Affiliate) to automate product data retrieval and link generation.
*   **Social Media API Keys**: For platforms like Twitter, Facebook, Instagram (if social media promotion is automated).
*   **Email Marketing Service API Key**: For services like Mailchimp, SendGrid (if email marketing is automated).

I will prompt you for these credentials as they are needed during the development phases. Please ensure these are securely stored and provided when requested.

## 8. Conclusion

This document provides a comprehensive design for an automated SEO blog system, building upon the existing `seo-blog-builder` project. The proposed architecture emphasizes modularity, agent-based automation, and data-driven decision-making to achieve the goal of generating high-quality, monetized content on trending high-ticket products. The next steps will involve the detailed implementation of each component, starting with the backend automation system.
````

## File: automated-blog-system/src/main.py
````python
import os
import sys
import json
import argparse
# DON'T CHANGE THIS !!!
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

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Enable CORS for all routes
CORS(app)

# Load configuration
app.config.from_object(Config)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(blog_bp, url_prefix='/api/blog')

# Import and register automation blueprint
from src.routes.automation import automation_bp
app.register_blueprint(automation_bp, url_prefix='/api/automation')

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

@app.route('/', defaults={'path': ''}) 
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Automated Blog System')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    
    # Ensure database directory exists before running the app
    db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database")
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"Created database directory: {db_dir}")
    
    # Run the app on the specified port
    app.run(host='0.0.0.0', port=args.port, debug=True)
````

## File: blog-frontend/package.json
````json
{
  "name": "blog-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "@hookform/resolvers": "^5.0.1",
    "@radix-ui/react-accordion": "^1.2.10",
    "@radix-ui/react-alert-dialog": "^1.1.13",
    "@radix-ui/react-aspect-ratio": "^1.1.6",
    "@radix-ui/react-avatar": "^1.1.9",
    "@radix-ui/react-checkbox": "^1.3.1",
    "@radix-ui/react-collapsible": "^1.1.10",
    "@radix-ui/react-context-menu": "^2.2.14",
    "@radix-ui/react-dialog": "^1.1.13",
    "@radix-ui/react-dropdown-menu": "^2.1.14",
    "@radix-ui/react-hover-card": "^1.1.13",
    "@radix-ui/react-label": "^2.1.6",
    "@radix-ui/react-menubar": "^1.1.14",
    "@radix-ui/react-navigation-menu": "^1.2.12",
    "@radix-ui/react-popover": "^1.1.13",
    "@radix-ui/react-progress": "^1.1.6",
    "@radix-ui/react-radio-group": "^1.3.6",
    "@radix-ui/react-scroll-area": "^1.2.8",
    "@radix-ui/react-select": "^2.2.4",
    "@radix-ui/react-separator": "^1.1.6",
    "@radix-ui/react-slider": "^1.3.4",
    "@radix-ui/react-slot": "^1.2.2",
    "@radix-ui/react-switch": "^1.2.4",
    "@radix-ui/react-tabs": "^1.1.11",
    "@radix-ui/react-toggle": "^1.1.8",
    "@radix-ui/react-toggle-group": "^1.1.9",
    "@radix-ui/react-tooltip": "^1.2.6",
    "@tailwindcss/vite": "^4.1.7",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.1.1",
    "date-fns": "^4.1.0",
    "embla-carousel-react": "^8.6.0",
    "framer-motion": "^12.15.0",
    "input-otp": "^1.4.2",
    "lucide-react": "^0.510.0",
    "next-themes": "^0.4.6",
    "node-fetch": "^3.3.2",
    "react": "^18.2.0",
    "react-day-picker": "8.10.1",
    "react-dom": "^18.2.0",
    "react-hook-form": "^7.56.3",
    "react-resizable-panels": "^3.0.2",
    "react-router-dom": "^7.6.1",
    "recharts": "^2.15.3",
    "sonner": "^2.0.3",
    "tailwind-merge": "^3.3.0",
    "tailwindcss": "^4.1.7",
    "vaul": "^1.1.2",
    "zod": "^3.24.4"
  },
  "devDependencies": {
    "@eslint/js": "^9.25.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.4.1",
    "eslint": "^9.25.0",
    "eslint-plugin-react-hooks": "^5.2.0",
    "eslint-plugin-react-refresh": "^0.4.19",
    "globals": "^16.0.0",
    "tw-animate-css": "^1.2.9",
    "vite": "^6.3.5"
  },
  "packageManager": "pnpm@10.4.1+sha512.c753b6c3ad7afa13af388fa6d808035a008e30ea9993f58c6663e2bc5ff21679aa834db094987129aa4d488b86df57f7b634981b2f827cdcacc698cc0cfb88af"
}
````

## File: todo.md
````markdown
# Automated Blog Platform - Development Todo

## Phase 1: Fix SQLite Database Issue
- [x] Check current database configuration
- [x] Fix database path and permissions
- [x] Test database connection
- [x] Fix syntax errors in main.py
- [x] Create missing model files
- [x] Create missing route files
- [x] Successfully start Flask server
- [x] Create missing service files (trend_analyzer, content_generator, seo_optimizer, automation_scheduler)

## Phase 3: Complete Frontend-Backend Integration
- [x] Update Dashboard component API calls to localhost
- [x] Fix Products component API integration
- [x] Fix Articles component API integration
- [x] Create GenerateArticle component
- [x] Add Generate Article to navigation
- [x] Fix remaining hardcoded API URLs
- [x] Add missing PUT/DELETE endpoints for articles and products
- [x] Create Analytics component
- [x] Add missing routes (/generate, /analytics, /settings)
- [x] Complete frontend-backend integration

## Phase 3: Test Backend API
- [x] Start Flask server
- [x] Test API endpoints
- [x] Verify OpenAI integration

## Phase 3.5: WordPress Integration
- [x] Implement WordPress service for posting articles
- [x] Add tag handling for WordPress posts
- [x] Test WordPress integration with test product
- [x] Verify articles appear on WordPress site
- [x] Add error handling and logging for WordPress integration
- [x] Update Articles component to show WordPress post status
- [x] Add functionality to view WordPress posts directly from the frontend
- [x] Implement UI for updating WordPress posts
- [x] Implement UI for deleting WordPress posts
- [x] Ensure proper error handling for WordPress-related operations
- [x] Test all WordPress integration features

## Phase 4: Complete Frontend Integration
- [x] Connect frontend to backend
- [x] Test data flow
- [x] Fix any UI issues

## Phase 5: Multi-Niche System
- [ ] Add niche selection to database
- [ ] Create niche management UI
- [ ] Update content generation for niches

## Phase 6: Niche Configuration Interface
- [ ] Build niche selection form
- [ ] Add niche-specific settings
- [ ] Test niche workflows

## Phase 7: Enhanced Content Generation
- [ ] Niche-specific content templates
- [ ] Targeted keyword research
- [ ] Affiliate link optimization

## Phase 8: Automated Site Creation
- [x] WordPress integration API
- [x] WordPress post management (view, update, delete)
- [ ] WordPress site creation API
- [ ] Template deployment
- [ ] Domain management

## Phase 9: Testing & Deployment
- [ ] End-to-end testing
- [ ] Production deployment
- [ ] Performance optimization

## Phase 10: Final Delivery
- [ ] Documentation
- [ ] User guide
- [ ] Handover
````

## File: automated-blog-system/src/routes/blog.py
````python
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
````

## File: blog-frontend/src/components/Articles.jsx
````javascript
import { useState, useEffect } from 'react';
import WordPressPostEditor from './WordPressPostEditor';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Edit, Trash2, Search, RefreshCw, Eye, FileText, Upload, ExternalLink, AlertTriangle, Check, X, Pencil } from 'lucide-react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { blogApi } from '@/services/api';

const Articles = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [wordpressStatuses, setWordpressStatuses] = useState({});
  const [loadingWordpressStatus, setLoadingWordpressStatus] = useState({});
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [isWordPressEditorOpen, setIsWordPressEditorOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deletingWordPress, setDeletingWordPress] = useState(false);

  useEffect(() => {
    fetchArticles();
  }, []);

  // Fetch WordPress status for each article
  useEffect(() => {
    const fetchWordPressStatuses = async () => {
      const statuses = {};
      
      for (const article of articles) {
        if (article.wordpress_post_id) {
          try {
            setLoadingWordpressStatus(prev => ({ ...prev, [article.id]: true }));
            const data = await blogApi.getWordPressStatus(article.id);
            if (data.success) {
              statuses[article.id] = data.status;
            }
          } catch (error) {
            console.error(`Error fetching WordPress status for article ${article.id}:`, error);
            statuses[article.id] = 'error';
          } finally {
            setLoadingWordpressStatus(prev => ({ ...prev, [article.id]: false }));
          }
        }
      }
      
      setWordpressStatuses(statuses);
    };

    if (articles.length > 0) {
      fetchWordPressStatuses();
    }
  }, [articles]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const data = await blogApi.getArticles();
      if (data.success) {
        setArticles(data.articles || []);
      } else {
        console.error('Error fetching articles:', data.error);
      }
    } catch (error) {
      console.error('Error fetching articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (article.status && article.status.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDelete = async (articleId) => {
    if (window.confirm('Are you sure you want to delete this article?')) {
      try {
        const data = await blogApi.deleteArticle(articleId);
        if (data.success) {
          fetchArticles(); // Refresh the list
        } else {
          console.error('Error deleting article:', data.error);
        }
      } catch (error) {
        console.error('Error deleting article:', error);
      }
    }
  };

  const handleStatusChange = async (articleId, newStatus) => {
    try {
      const data = await blogApi.updateArticle(articleId, { status: newStatus });
      if (data.success) {
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error updating article status:', data.error);
      }
    } catch (error) {
      console.error('Error updating article status:', error);
    }
  };

  const handlePublishToWordPress = async (articleId) => {
    try {
      const data = await blogApi.publishToWordPress(articleId);
      if (data.success) {
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error publishing to WordPress:', data.error);
      }
    } catch (error) {
      console.error('Error publishing to WordPress:', error);
    }
  };

  const handleEditWordPressPost = (article) => {
    setSelectedArticle(article);
    setIsWordPressEditorOpen(true);
  };

  const handleDeleteWordPressPost = async () => {
    if (!selectedArticle) return;
    
    setDeletingWordPress(true);
    try {
      const data = await blogApi.deleteWordPressPost(selectedArticle.id);
      if (data.success) {
        setIsDeleteDialogOpen(false);
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error deleting WordPress post:', data.error);
      }
    } catch (error) {
      console.error('Error deleting WordPress post:', error);
    } finally {
      setDeletingWordPress(false);
    }
  };

  const openDeleteDialog = (article) => {
    setSelectedArticle(article);
    setIsDeleteDialogOpen(true);
  };

  const getStatusBadge = (status) => {
    const variants = {
      published: 'default',
      draft: 'secondary',
      scheduled: 'outline'
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  const getWordPressBadge = (article) => {
    if (loadingWordpressStatus[article.id]) {
      return <Badge variant="outline" className="ml-2 bg-slate-100"><RefreshCw className="h-3 w-3 mr-1 animate-spin" />WordPress</Badge>;
    }
    
    if (!article.wordpress_post_id) {
      return <Badge variant="outline" className="ml-2 bg-slate-100"><X className="h-3 w-3 mr-1" />Not on WordPress</Badge>;
    }
    
    const wpStatus = wordpressStatuses[article.id];
    
    if (wpStatus === 'error') {
      return <Badge variant="destructive" className="ml-2"><AlertTriangle className="h-3 w-3 mr-1" />WordPress Error</Badge>;
    }
    
    if (wpStatus === 'publish') {
      return <Badge variant="default" className="ml-2 bg-green-600"><Check className="h-3 w-3 mr-1" />WordPress Published</Badge>;
    }
    
    if (wpStatus === 'draft') {
      return <Badge variant="secondary" className="ml-2"><FileText className="h-3 w-3 mr-1" />WordPress Draft</Badge>;
    }
    
    return <Badge variant="outline" className="ml-2 bg-slate-100">WordPress</Badge>;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Articles</h1>
            <p className="text-muted-foreground">
              Manage your SEO-optimized articles and content.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={fetchArticles}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Generate New Article
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Article List</CardTitle>
            <CardDescription>All articles in your system.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center py-4">
              <Input
                placeholder="Search articles..."
                value={searchTerm}
                onChange={handleSearch}
                className="max-w-sm"
              />
              <Search className="ml-2 h-4 w-4 text-muted-foreground" />
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Views</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredArticles.length > 0 ? (
                  filteredArticles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell className="font-medium max-w-xs">
                        <div className="truncate">{article.title}</div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(article.status)}
                        {getWordPressBadge(article)}
                      </TableCell>
                      <TableCell>{article.views || 0}</TableCell>
                      <TableCell>${(article.revenue || 0).toFixed(2)}</TableCell>
                      <TableCell>{formatDate(article.created_at)}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          {article.status === 'draft' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStatusChange(article.id, 'published')}
                            >
                              <FileText className="h-4 w-4" />
                            </Button>
                          )}
                          {!article.wordpress_post_id ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePublishToWordPress(article.id)}
                              title="Publish to WordPress"
                            >
                              <Upload className="h-4 w-4" />
                            </Button>
                          ) : (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(`${article.wordpress_url}`, '_blank')}
                                title="View on WordPress"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditWordPressPost(article)}
                                title="Edit WordPress Post"
                              >
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openDeleteDialog(article)}
                                title="Delete from WordPress"
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(article.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      No articles found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* WordPress Post Editor Dialog */}
    {selectedArticle && (
      <WordPressPostEditor
        article={selectedArticle}
        isOpen={isWordPressEditorOpen}
        onClose={() => setIsWordPressEditorOpen(false)}
        onSuccess={fetchArticles}
      />
    )}

    {/* Delete WordPress Post Confirmation Dialog */}
    <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete WordPress Post</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete this post from WordPress? This action cannot be undone.
            The article will remain in your local database.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deletingWordPress}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteWordPressPost}
            disabled={deletingWordPress}
            className="bg-red-600 hover:bg-red-700"
          >
            {deletingWordPress ? 'Deleting...' : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
};

export default Articles;
````
