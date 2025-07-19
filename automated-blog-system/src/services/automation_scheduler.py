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

