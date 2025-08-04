import React, { useState, useEffect } from 'react';
import { blogApi } from '@/services/api';

const NichesSimple = () => {
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchNiches();
  }, []);

  const fetchNiches = async () => {
    console.log('NichesSimple: Starting fetchNiches...');
    setLoading(true);
    try {
      console.log('NichesSimple: Calling blogApi.getNiches()...');
      const data = await blogApi.getNiches();
      console.log('NichesSimple: API Response:', data);
      if (data.success) {
        console.log('NichesSimple: Setting niches:', data.niches);
        setNiches(data.niches || []);
      } else {
        console.error('NichesSimple: API returned success=false:', data.error);
        setError('Failed to fetch niches: ' + data.error);
      }
    } catch (error) {
      console.error('NichesSimple: Error fetching niches:', error);
      setError('Error fetching niches. Please try again.');
    } finally {
      console.log('NichesSimple: Setting loading=false');
      setLoading(false);
    }
  };

  const filteredNiches = niches.filter(niche =>
    niche.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (niche.description && niche.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  console.log('NichesSimple: Rendering with state:', { 
    loading, 
    error, 
    nichesCount: niches.length, 
    filteredCount: filteredNiches.length 
  });

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Niches - Loading...</h1>
        <p>Fetching niches from API...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Niches - Error</h1>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
        <button 
          onClick={fetchNiches}
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
        <h1 className="text-3xl font-bold mb-2">Niches</h1>
        <p className="text-gray-600 mb-4">Manage your content niches and market segments.</p>
        
        <div className="flex gap-4 mb-4">
          <button 
            onClick={fetchNiches}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
          >
            🔄 Refresh
          </button>
          <button 
            onClick={() => alert('Add Niche functionality coming soon!')}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            ➕ Add New Niche
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Niche List ({filteredNiches.length})</h2>
        
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search niches..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {filteredNiches.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Profitability</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Competition</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredNiches.map((niche) => (
                  <tr key={niche.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{niche.name}</div>
                      {niche.keywords && (
                        <div className="text-sm text-gray-500">
                          Keywords: {niche.keywords.split(',').slice(0, 3).join(', ')}
                          {niche.keywords.split(',').length > 3 && '...'}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 max-w-xs">
                        {niche.description ? (
                          niche.description.length > 100 ? 
                            niche.description.substring(0, 100) + '...' : 
                            niche.description
                        ) : 'No description'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">
                          {niche.profitability_score}/100
                        </div>
                        <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              niche.profitability_score >= 80 ? 'bg-green-500' :
                              niche.profitability_score >= 60 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${niche.profitability_score}%` }}
                          ></div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        niche.competition_level === 'low' ? 'bg-green-100 text-green-800' :
                        niche.competition_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {niche.competition_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        niche.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {niche.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        onClick={() => alert(`Edit niche: ${niche.name}`)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        ✏️ Edit
                      </button>
                      <button 
                        onClick={() => {
                          if (window.confirm(`Delete niche: ${niche.name}?`)) {
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
            <p className="text-gray-500">No niches found.</p>
            {searchTerm ? (
              <p className="text-sm text-gray-400 mt-2">
                Try adjusting your search term.
              </p>
            ) : (
              <p className="text-sm text-gray-400 mt-2">
                Create your first niche to get started!
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default NichesSimple;
