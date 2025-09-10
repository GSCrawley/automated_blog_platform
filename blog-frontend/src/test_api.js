/**
 * Test script for core API endpoints (WordPress integration removed)
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
  // WordPress endpoints removed
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