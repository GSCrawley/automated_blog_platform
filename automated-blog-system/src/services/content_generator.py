import os
import openai
from typing import Dict, Any, List
from src.config import Config

class ContentGenerator:
    """Service for generating SEO-optimized blog content."""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(
            api_key=Config.OPENAI_API_KEY
        ) if Config.OPENAI_API_KEY else None
    
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

