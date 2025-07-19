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

