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

