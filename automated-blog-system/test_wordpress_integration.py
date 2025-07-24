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