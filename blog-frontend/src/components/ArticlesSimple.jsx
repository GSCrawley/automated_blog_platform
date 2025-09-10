import React, { useState, useEffect } from 'react';
import { blogApi } from '@/services/api';

const ArticlesSimple = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    console.log('ArticlesSimple: Starting fetchArticles...');
    setLoading(true);
    try {
      console.log('ArticlesSimple: Calling blogApi.getArticles()...');
      const data = await blogApi.getArticles();
      console.log('ArticlesSimple: API Response:', data);
      if (data.success) {
        console.log('ArticlesSimple: Setting articles:', data.articles);
        setArticles(data.articles || []);
      } else {
        console.error('ArticlesSimple: API returned success=false:', data.error);
        setError('Failed to fetch articles: ' + data.error);
      }
    } catch (error) {
      console.error('ArticlesSimple: Error fetching articles:', error);
      setError('Error fetching articles. Please try again.');
    } finally {
      console.log('ArticlesSimple: Setting loading=false');
      setLoading(false);
    }
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (article.category && article.category.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (article.tags && article.tags.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  console.log('ArticlesSimple: Rendering with state:', { 
    loading, 
    error, 
    articlesCount: articles.length, 
    filteredCount: filteredArticles.length 
  });

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Articles - Loading...</h1>
        <p>Fetching articles from API...</p>
      </div>
    );
  }

  if (error) {
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
            onClick={() => alert('Add Article functionality coming soon!')}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            ➕ Add New Article
          </button>
        </div>
      </div>

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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  {/* WordPress column removed */}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {article.category || 'N/A'}
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
                    {/* WordPress status removed */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {article.created_at ? new Date(article.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        onClick={() => alert(`Edit article: ${article.title}`)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        onClick={() => {
                          if (window.confirm(`Delete article: ${article.title}?`)) {
                            alert('Delete functionality coming soon!');
                          }
                        }}
                        className="text-red-600 hover:text-red-900"
                      >
                        🗑️ Delete
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
