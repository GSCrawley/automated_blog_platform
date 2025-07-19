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

