import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { blogApi } from '@/services/api';

const ArticlesSimple = () => {
  const [articles, setArticles] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    meta_description: '',
    product_id: '',
    niche_id: '',
    status: 'draft',
    keywords: ''
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [editingArticle, setEditingArticle] = useState(null);
  const [showEditForm, setShowEditForm] = useState(false);

  useEffect(() => {
    fetchArticles();
    fetchProducts();
  }, []);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const data = await blogApi.getArticles();
      if (data.success) {
        setArticles(data.articles || []);
      } else {
        setError('Failed to fetch articles: ' + data.error);
      }
    } catch {
      setError('Error fetching articles. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const data = await blogApi.getProducts();
      if (data.success) {
        setProducts(data.products || []);
      }
    } catch {
      console.error('Error fetching products:', error);
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.title.trim()) {
      errors.title = 'Title is required';
    }

    if (!formData.content.trim()) {
      errors.content = 'Content is required';
    }

    if (!formData.product_id) {
      errors.product_id = 'Product is required';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

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
      const articleData = {
        ...formData,
        product_id: parseInt(formData.product_id),
        niche_id: formData.niche_id ? parseInt(formData.niche_id) : null,
        keywords: formData.keywords ? formData.keywords.split(',').map(k => k.trim()) : []
      };

      const response = await blogApi.createArticle(articleData);

      if (response.success) {
        setArticles(prev => [...prev, response.article]);
        resetForm();
        setError(null);
      } else {
        setError('Failed to create article: ' + (response.error || 'Unknown error'));
      }
    } catch {
      setError('Error creating article. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      meta_description: '',
      product_id: '',
      niche_id: '',
      status: 'draft',
      keywords: ''
    });
    setFormErrors({});
    setShowAddForm(false);
  };

  const handleDelete = async (article) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${article.title}"?\n\nThis action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setDeleting(article.id);
    try {
      const response = await blogApi.deleteArticle(article.id);

      if (response.success) {
        setArticles(prev => prev.filter(a => a.id !== article.id));
        setError(null);
      } else {
        setError('Failed to delete article: ' + (response.error || 'Unknown error'));
      }
    } catch {
      setError('Error deleting article. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const handleEdit = (article) => {
    setEditingArticle(article);
    setFormData({
      title: article.title || '',
      content: article.content || '',
      meta_description: article.meta_description || '',
      product_id: article.product_id ? article.product_id.toString() : '',
      niche_id: article.niche_id ? article.niche_id.toString() : '',
      status: article.status || 'draft',
      keywords: article.keywords ? (typeof article.keywords === 'string' ? article.keywords : article.keywords.join(', ')) : ''
    });
    setFormErrors({});
    setShowEditForm(true);
    setShowAddForm(false);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();

    const errors = {};
    if (!formData.title.trim()) errors.title = 'Title is required';
    if (!formData.content.trim()) errors.content = 'Content is required';

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      const articleData = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        meta_description: formData.meta_description.trim(),
        status: formData.status,
        keywords: formData.keywords ? formData.keywords.split(',').map(k => k.trim()) : []
      };

      const response = await blogApi.updateArticle(editingArticle.id, articleData);

      if (response.success) {
        setArticles(prev => prev.map(a =>
          a.id === editingArticle.id ? { ...a, ...articleData } : a
        ));
        resetEditForm();
        setError(null);
      } else {
        setError('Failed to update article: ' + (response.error || 'Unknown error'));
      }
    } catch {
      setError('Error updating article. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetEditForm = () => {
    resetForm();
    setEditingArticle(null);
    setShowEditForm(false);
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (article.status && article.status.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Articles - Loading...</h1>
        <p>Fetching articles from API...</p>
      </div>
    );
  }

  if (error && !showAddForm && !showEditForm) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Articles - Error</h1>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button
          onClick={fetchArticles}
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
        <h1 className="text-3xl font-bold mb-2">Articles</h1>
        <p className="text-gray-600 mb-4">Manage your blog articles and content.</p>

        <div className="flex gap-4 mb-4">
          <button
            onClick={fetchArticles}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            ➕ Add New Article
          </button>
        </div>
      </div>

      {/* Add Article Form */}
      {showAddForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add New Article</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.title ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter article title"
              />
              {formErrors.title && (
                <p className="text-red-500 text-sm mt-1">{formErrors.title}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content *
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                rows={8}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.content ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter article content..."
              />
              {formErrors.content && (
                <p className="text-red-500 text-sm mt-1">{formErrors.content}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meta Description
              </label>
              <input
                type="text"
                name="meta_description"
                value={formData.meta_description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Brief description for SEO"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product *
                </label>
                <select
                  name="product_id"
                  value={formData.product_id}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formErrors.product_id ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select a product</option>
                  {products.map(product => (
                    <option key={product.id} value={product.id}>
                      {product.name}
                    </option>
                  ))}
                </select>
                {formErrors.product_id && (
                  <p className="text-red-500 text-sm mt-1">{formErrors.product_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Keywords (comma-separated)
              </label>
              <input
                type="text"
                name="keywords"
                value={formData.keywords}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., review, best, 2024"
              />
            </div>

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
                {submitting ? 'Creating...' : 'Create Article'}
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

      {/* Edit Article Form */}
      {showEditForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Edit Article</h2>
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.title ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter article title"
              />
              {formErrors.title && (
                <p className="text-red-500 text-sm mt-1">{formErrors.title}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content *
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                rows={8}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.content ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter article content..."
              />
              {formErrors.content && (
                <p className="text-red-500 text-sm mt-1">{formErrors.content}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Meta Description
              </label>
              <input
                type="text"
                name="meta_description"
                value={formData.meta_description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Brief description for SEO"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Keywords (comma-separated)
              </label>
              <input
                type="text"
                name="keywords"
                value={formData.keywords}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., review, best, 2024"
              />
            </div>

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
                {submitting ? 'Updating...' : 'Update Article'}
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
        <h2 className="text-xl font-semibold mb-4">Article List ({filteredArticles.length})</h2>

        <div className="mb-4">
          <input
            type="text"
            placeholder="Search articles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {filteredArticles.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredArticles.map((article) => (
                  <tr key={article.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{article.title}</div>
                      {article.meta_description && (
                        <div className="text-sm text-gray-500 max-w-xs truncate">
                          {article.meta_description}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        article.status === 'published' ? 'bg-green-100 text-green-800' :
                        article.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {article.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {article.created_at ? new Date(article.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/articles/${article.id}/editor`}
                        className="text-purple-600 hover:text-purple-900 mr-3 font-medium"
                        title="Open in visual editor with live preview"
                      >
                        👁 Preview &amp; Edit
                      </Link>
                      <button
                        onClick={() => handleEdit(article)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDelete(article)}
                        disabled={deleting === article.id}
                        className={`text-red-600 hover:text-red-900 ${
                          deleting === article.id ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {deleting === article.id ? '⏳ Deleting...' : '🗑️ Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No articles found.</p>
            {searchTerm ? (
              <p className="text-sm text-gray-400 mt-2">
                Try adjusting your search term.
              </p>
            ) : (
              <p className="text-sm text-gray-400 mt-2">
                Create your first article to get started!
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ArticlesSimple;
