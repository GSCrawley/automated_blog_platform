import React, { useState, useEffect } from 'react';
import { blogApi } from '@/services/api';

const ProductsSimple = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    price: '',
    currency: 'USD',
    category: '',
    competition_level: 'medium',
    trend_score: '',
    niche_id: ''
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(null); // Track which product is being deleted
  const [editingProduct, setEditingProduct] = useState(null);
  const [showEditForm, setShowEditForm] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    console.log('ProductsSimple: Starting fetchProducts...');
    setLoading(true);
    try {
      console.log('ProductsSimple: Calling blogApi.getProducts()...');
      const data = await blogApi.getProducts();
      console.log('ProductsSimple: API Response:', data);
      if (data.success) {
        console.log('ProductsSimple: Setting products:', data.products);
        setProducts(data.products || []);
      } else {
        console.error('ProductsSimple: API returned success=false:', data.error);
        setError('Failed to fetch products: ' + data.error);
      }
    } catch (error) {
      console.error('ProductsSimple: Error fetching products:', error);
      setError('Error fetching products. Please try again.');
    } finally {
      console.log('ProductsSimple: Setting loading=false');
      setLoading(false);
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Product name is required';
    }
    
    if (!formData.price || isNaN(formData.price) || parseFloat(formData.price) <= 0) {
      errors.price = 'Valid price is required';
    }
    
    if (!formData.category.trim()) {
      errors.category = 'Category is required';
    }
    
    if (formData.trend_score && (isNaN(formData.trend_score) || parseFloat(formData.trend_score) < 0 || parseFloat(formData.trend_score) > 100)) {
      errors.trend_score = 'Trend score must be between 0 and 100';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error for this field when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    try {
      console.log('ProductsSimple: Creating product:', formData);
      const response = await blogApi.createProduct({
        ...formData,
        price: parseFloat(formData.price),
        trend_score: formData.trend_score ? parseFloat(formData.trend_score) : null,
        niche_id: formData.niche_id || null
      });
      
      console.log('ProductsSimple: Create response:', response);
      if (response.success) {
        // Add new product to the list
        setProducts(prev => [...prev, response.product]);
        // Reset form
        setFormData({
          name: '',
          price: '',
          currency: 'USD',
          category: '',
          competition_level: 'medium',
          trend_score: '',
          niche_id: ''
        });
        setShowAddForm(false);
        setError(null);
      } else {
        setError('Failed to create product: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('ProductsSimple: Error creating product:', error);
      setError('Error creating product. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      price: '',
      currency: 'USD',
      category: '',
      competition_level: 'medium',
      trend_score: '',
      niche_id: ''
    });
    setFormErrors({});
    setShowAddForm(false);
  };

  const handleDelete = async (product) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${product.name}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmed) {
      return;
    }
    
    setDeleting(product.id);
    try {
      console.log('ProductsSimple: Deleting product:', product.id);
      const response = await blogApi.deleteProduct(product.id);
      console.log('ProductsSimple: Delete response:', response);
      
      if (response.success) {
        // Remove product from the list
        setProducts(prev => prev.filter(p => p.id !== product.id));
        setError(null);
      } else {
        setError('Failed to delete product: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('ProductsSimple: Error deleting product:', error);
      setError('Error deleting product. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const handleEdit = (product) => {
    console.log('ProductsSimple: Starting edit for product:', product);
    setEditingProduct(product);
    // Pre-populate form with existing product data
    setFormData({
      name: product.name || '',
      price: product.price ? product.price.toString() : '',
      currency: product.currency || 'USD',
      category: product.category || '',
      competition_level: product.competition_level || 'medium',
      trend_score: product.trend_score ? product.trend_score.toString() : '',
      niche_id: product.niche_id ? product.niche_id.toString() : ''
    });
    setFormErrors({});
    setShowEditForm(true);
    setShowAddForm(false); // Hide add form if open
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields
    const errors = {};
    if (!formData.name.trim()) errors.name = 'Product name is required';
    if (!formData.price || parseFloat(formData.price) <= 0) errors.price = 'Valid price is required';
    if (!formData.category.trim()) errors.category = 'Category is required';
    
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    
    setIsSubmitting(true);
    try {
      console.log('ProductsSimple: Updating product:', editingProduct.id, formData);
      
      const productData = {
        name: formData.name.trim(),
        price: parseFloat(formData.price),
        currency: formData.currency,
        category: formData.category.trim(),
        competition_level: formData.competition_level,
        trend_score: formData.trend_score ? parseFloat(formData.trend_score) : null,
        niche_id: formData.niche_id ? parseInt(formData.niche_id) : null
      };
      
      const response = await blogApi.updateProduct(editingProduct.id, productData);
      console.log('ProductsSimple: Update response:', response);
      
      if (response.success) {
        // Update the product in the list
        setProducts(prev => prev.map(p => 
          p.id === editingProduct.id ? { ...p, ...productData } : p
        ));
        resetEditForm();
        setError(null);
      } else {
        setError('Failed to update product: ' + (response.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('ProductsSimple: Error updating product:', error);
      setError('Error updating product. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetEditForm = () => {
    setFormData({
      name: '',
      price: '',
      currency: 'USD',
      category: '',
      competition_level: 'medium',
      trend_score: '',
      niche_id: ''
    });
    setFormErrors({});
    setEditingProduct(null);
    setShowEditForm(false);
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (product.category && product.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  console.log('ProductsSimple: Rendering with state:', { 
    loading, 
    error, 
    productsCount: products.length, 
    filteredCount: filteredProducts.length 
  });

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Products - Loading...</h1>
        <p>Fetching products from API...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Products - Error</h1>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button 
          onClick={fetchProducts}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Products</h1>
        <p className="text-gray-600 mb-4">Manage your high-ticket products for content generation.</p>
        
        <div className="flex gap-4 mb-4">
          <button 
            onClick={fetchProducts}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
          >
            🔄 Refresh
          </button>
          <button 
            onClick={() => setShowAddForm(true)}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            ➕ Add New Product
          </button>
        </div>
      </div>

      {/* Add Product Form */}
      {showAddForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add New Product</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Product Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formErrors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter product name"
                />
                {formErrors.name && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.name}</p>
                )}
              </div>

              {/* Price */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Price *
                </label>
                <div className="flex">
                  <select
                    name="currency"
                    value={formData.currency}
                    onChange={handleInputChange}
                    className="px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleInputChange}
                    step="0.01"
                    min="0"
                    className={`flex-1 px-3 py-2 border rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      formErrors.price ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="0.00"
                  />
                </div>
                {formErrors.price && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.price}</p>
                )}
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formErrors.category ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., Electronics, Health, etc."
                />
                {formErrors.category && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.category}</p>
                )}
              </div>

              {/* Competition Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Competition Level
                </label>
                <select
                  name="competition_level"
                  value={formData.competition_level}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              {/* Trend Score */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trend Score (0-100)
                </label>
                <input
                  type="number"
                  name="trend_score"
                  value={formData.trend_score}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formErrors.trend_score ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Optional trend score"
                />
                {formErrors.trend_score && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.trend_score}</p>
                )}
              </div>

              {/* Niche ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Niche ID
                </label>
                <input
                  type="number"
                  name="niche_id"
                  value={formData.niche_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional niche ID"
                />
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                disabled={submitting}
                className={`px-6 py-2 rounded-md text-white font-medium ${
                  submitting
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600'
                }`}
              >
                {submitting ? 'Creating...' : 'Create Product'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-md font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Product Form */}
      {showEditForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Edit Product</h2>
          
          <form onSubmit={handleEditSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Product Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formErrors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter product name"
                />
                {formErrors.name && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.name}</p>
                )}
              </div>

              {/* Price */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Price *
                </label>
                <div className="flex">
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleInputChange}
                    step="0.01"
                    min="0"
                    className={`flex-1 px-3 py-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      formErrors.price ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="0.00"
                  />
                  <select
                    name="currency"
                    value={formData.currency}
                    onChange={handleInputChange}
                    className="px-3 py-2 border-l-0 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                </div>
                {formErrors.price && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.price}</p>
                )}
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formErrors.category ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="Enter product category"
                />
                {formErrors.category && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.category}</p>
                )}
              </div>

              {/* Competition Level */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Competition Level
                </label>
                <select
                  name="competition_level"
                  value={formData.competition_level}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              {/* Trend Score */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trend Score (0-100)
                </label>
                <input
                  type="number"
                  name="trend_score"
                  value={formData.trend_score}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional trend score"
                />
              </div>

              {/* Niche ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Niche ID
                </label>
                <input
                  type="number"
                  name="niche_id"
                  value={formData.niche_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional niche ID"
                />
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className={`px-6 py-2 rounded-md text-white font-medium ${
                  isSubmitting
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600'
                }`}
              >
                {isSubmitting ? 'Updating...' : 'Update Product'}
              </button>
              <button
                type="button"
                onClick={resetEditForm}
                className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-md font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Product List ({filteredProducts.length})</h2>
        
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {filteredProducts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Competition</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Niche</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredProducts.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{product.name}</div>
                      {product.trend_score && (
                        <div className="text-sm text-gray-500">
                          Trend Score: {product.trend_score.toFixed(1)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.category || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.currency} {product.price}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        product.competition_level === 'low' ? 'bg-green-100 text-green-800' :
                        product.competition_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {product.competition_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.niche_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        onClick={() => handleEdit(product)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        onClick={() => handleDelete(product)}
                        disabled={deleting === product.id}
                        className={`text-red-600 hover:text-red-900 ${
                          deleting === product.id ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {deleting === product.id ? '⏳ Deleting...' : '🗑️ Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No products found.</p>
            {searchTerm && (
              <p className="text-sm text-gray-400 mt-2">
                Try adjusting your search term.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductsSimple;
