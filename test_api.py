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