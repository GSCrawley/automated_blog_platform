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