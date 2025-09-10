/**
 * Test script for core API endpoints (WordPress removed)
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
  
  // WordPress endpoints removed
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

  // WordPress integration tests removed

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