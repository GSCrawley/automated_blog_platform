import React, { useState, useEffect } from 'react';
import { blogApi } from '@/services/api';

const NichesSimple = () => {
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_keywords: '',
    competition_level: 'medium',
    profitability_score: 50
  });
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [editingNiche, setEditingNiche] = useState(null);
  const [showEditForm, setShowEditForm] = useState(false);

  useEffect(() => {
    fetchNiches();
  }, []);

  const fetchNiches = async () => {
    setLoading(true);
    try {
      const data = await blogApi.getNiches();
      if (data.success) {
        setNiches(data.niches || []);
      } else {
        setError('Failed to fetch niches: ' + data.error);
      }
    } catch {
      setError('Error fetching niches. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.name.trim()) {
      errors.name = 'Niche name is required';
    }

    if (!formData.description.trim()) {
      errors.description = 'Description is required';
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
      const nicheData = {
        ...formData,
        profitability_score: parseInt(formData.profitability_score)
      };

      const response = await blogApi.createNiche(nicheData);

      if (response.success) {
        setNiches(prev => [...prev, response.niche]);
        resetForm();
        setError(null);
      } else {
        setError('Failed to create niche: ' + (response.error || 'Unknown error'));
      }
    } catch {
      setError('Error creating niche. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      target_keywords: '',
      competition_level: 'medium',
      profitability_score: 50
    });
    setFormErrors({});
    setShowAddForm(false);
  };

  const handleDelete = async (niche) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${niche.name}"?\n\nThis action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setDeleting(niche.id);
    try {
      const response = await blogApi.deleteNiche(niche.id);

      if (response.success) {
        setNiches(prev => prev.filter(n => n.id !== niche.id));
        setError(null);
      } else {
        setError('Failed to delete niche: ' + (response.error || 'Unknown error'));
      }
    } catch {
      setError('Error deleting niche. Please try again.');
    } finally {
      setDeleting(null);
    }
  };

  const handleEdit = (niche) => {
    setEditingNiche(niche);
    setFormData({
      name: niche.name || '',
      description: niche.description || '',
      target_keywords: niche.target_keywords || '',
      competition_level: niche.competition_level || 'medium',
      profitability_score: niche.profitability_score || 50
    });
    setFormErrors({});
    setShowEditForm(true);
    setShowAddForm(false);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();

    const errors = {};
    if (!formData.name.trim()) errors.name = 'Niche name is required';
    if (!formData.description.trim()) errors.description = 'Description is required';

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setSubmitting(true);
    try {
      const nicheData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        target_keywords: formData.target_keywords.trim(),
        competition_level: formData.competition_level,
        profitability_score: parseInt(formData.profitability_score)
      };

      const response = await blogApi.updateNiche(editingNiche.id, nicheData);

      if (response.success) {
        setNiches(prev => prev.map(n =>
          n.id === editingNiche.id ? { ...n, ...nicheData } : n
        ));
        resetEditForm();
        setError(null);
      } else {
        setError('Failed to update niche: ' + (response.error || 'Unknown error'));
      }
    } catch {
      setError('Error updating niche. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const resetEditForm = () => {
    resetForm();
    setEditingNiche(null);
    setShowEditForm(false);
  };

  const filteredNiches = niches.filter(niche =>
    niche.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (niche.description && niche.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Niches - Loading...</h1>
        <p>Fetching niches from API...</p>
      </div>
    );
  }

  if (error && !showAddForm && !showEditForm) {
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
            onClick={() => setShowAddForm(true)}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            ➕ Add New Niche
          </button>
        </div>
      </div>

      {/* Add Niche Form */}
      {showAddForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add New Niche</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter niche name"
              />
              {formErrors.name && (
                <p className="text-red-500 text-sm mt-1">{formErrors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.description ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Describe this niche..."
              />
              {formErrors.description && (
                <p className="text-red-500 text-sm mt-1">{formErrors.description}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Keywords (comma-separated)
              </label>
              <input
                type="text"
                name="target_keywords"
                value={formData.target_keywords}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., best, review, guide"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Profitability Score (0-100)
                </label>
                <input
                  type="number"
                  name="profitability_score"
                  value={formData.profitability_score}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
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
                {submitting ? 'Creating...' : 'Create Niche'}
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

      {/* Edit Niche Form */}
      {showEditForm && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Edit Niche</h2>
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter niche name"
              />
              {formErrors.name && (
                <p className="text-red-500 text-sm mt-1">{formErrors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  formErrors.description ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Describe this niche..."
              />
              {formErrors.description && (
                <p className="text-red-500 text-sm mt-1">{formErrors.description}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Keywords (comma-separated)
              </label>
              <input
                type="text"
                name="target_keywords"
                value={formData.target_keywords}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., best, review, guide"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Profitability Score (0-100)
                </label>
                <input
                  type="number"
                  name="profitability_score"
                  value={formData.profitability_score}
                  onChange={handleInputChange}
                  min="0"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
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
                {submitting ? 'Updating...' : 'Update Niche'}
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredNiches.map((niche) => (
                  <tr key={niche.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{niche.name}</div>
                     {niche.target_keywords && (() => {
                        const keywords = Array.isArray(niche.target_keywords)
                         ? niche.target_keywords
                         : niche.target_keywords.split(',');
                      return (
                          <div className="text-sm text-gray-500">
                           {keywords.slice(0, 3).join(', ')}
                            {keywords.length > 3 && '...'}
                           </div>
                        );
                    })()}
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleEdit(niche)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => handleDelete(niche)}
                        disabled={deleting === niche.id}
                        className={`text-red-600 hover:text-red-900 ${
                          deleting === niche.id ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        {deleting === niche.id ? '⏳ Deleting...' : '🗑️ Delete'}
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
