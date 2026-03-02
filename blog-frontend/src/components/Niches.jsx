import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Target, Edit, Trash2, TrendingUp, Users, DollarSign, Loader2, RefreshCw, Rocket, CheckCircle2, AlertCircle } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { blogApi } from '@/services/api';

const Niches = () => {
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingNiche, setEditingNiche] = useState(null);
  const [activatingId, setActivatingId] = useState(null);
  const [activeNicheId, setActiveNicheId] = useState(null);
  const [automationSummary, setAutomationSummary] = useState(null);
  const [activationError, setActivationError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_keywords: '',
    target_audience: '',
    content_themes: '',
    affiliate_networks: '',
    competition_level: 'medium',
    profitability_score: 0,
    monetization_strategy: ''
  });

  useEffect(() => {
    fetchNiches();
  }, []);

  // Poll pipeline status for niches that are in-progress
  useEffect(() => {
    const activeNiches = niches.filter(
      n => n.pipeline_status === 'discovering_products' || n.pipeline_status === 'generating_articles'
    );
    if (activeNiches.length === 0) return;

    const interval = setInterval(() => {
      fetchNiches();
    }, 3000);
    return () => clearInterval(interval);
  }, [niches]);

  const fetchNiches = async () => {
    try {
      const data = await blogApi.getNiches();
      if (data.success) {
        setNiches(data.niches);
      }
    } catch (error) {
      console.error('Error fetching niches:', error);
    } finally {
      setLoading(false);
    }
  };

  const activateNiche = async (nicheId) => {
    setActivatingId(nicheId);
    setActivationError(null);
    try {
      const response = await fetch(`http://localhost:5000/api/agents/niches/${nicheId}/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });

      const data = await response.json();
      if (response.ok && data.status === 'success') {
        setActiveNicheId(nicheId);
        setAutomationSummary(data);
      } else {
        setActivationError(data.error || 'Failed to activate niche');
      }
    } catch (error) {
      console.error('Error activating niche:', error);
      setActivationError(error.message);
    } finally {
      setActivatingId(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = editingNiche
        ? await blogApi.updateNiche(editingNiche.id, formData)
        : await blogApi.createNiche(formData);

      if (data.success) {
        fetchNiches();
        setIsDialogOpen(false);
        resetForm();
      } else {
        console.error('Error creating/updating niche:', data.error);
      }
    } catch (error) {
      console.error('Error creating/updating niche:', error);
    }
  };

  const handleEdit = (niche) => {
    setEditingNiche(niche);
    setFormData({
      name: niche.name,
      description: niche.description || '',
      target_keywords: Array.isArray(niche.target_keywords) ? niche.target_keywords.join(', ') : niche.target_keywords || '',
      target_audience: niche.target_audience || '',
      content_themes: Array.isArray(niche.content_themes) ? niche.content_themes.join(', ') : niche.content_themes || '',
      affiliate_networks: Array.isArray(niche.affiliate_networks) ? niche.affiliate_networks.join(', ') : niche.affiliate_networks || '',
      competition_level: niche.competition_level || 'medium',
      profitability_score: niche.profitability_score || 0,
      monetization_strategy: niche.monetization_strategy || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (nicheId) => {
    if (window.confirm('Are you sure you want to delete this niche?')) {
      try {
        const data = await blogApi.deleteNiche(nicheId);
        if (data.success) {
          fetchNiches();
        }
      } catch (error) {
        console.error('Error deleting niche:', error);
      }
    }
  };

  const handleRunPipeline = async (nicheId) => {
    try {
      const data = await blogApi.runNichePipeline(nicheId);
      if (data.success) {
        fetchNiches();
      } else {
        console.error('Error running pipeline:', data.error);
      }
    } catch (error) {
      console.error('Error running pipeline:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      target_keywords: '',
      target_audience: '',
      content_themes: '',
      affiliate_networks: '',
      competition_level: 'medium',
      profitability_score: 0,
      monetization_strategy: ''
    });
    setEditingNiche(null);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading niches...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Niche Management</h1>
          <p className="text-gray-600 mt-2">Manage your blog niches and target markets</p>
        </div>
        <Dialog 
          open={isDialogOpen} 
          onOpenChange={(open) => {
            // Prevent closing on outside click - only allow programmatic close
            if (open) {
              setIsDialogOpen(true);
            }
          }}
        >
          <DialogTrigger asChild>
            <Button onClick={() => {
              resetForm();
              setIsDialogOpen(true);
            }} className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Niche
            </Button>
          </DialogTrigger>
          <DialogContent 
            className="max-w-2xl max-h-[90vh] overflow-y-auto"
            onPointerDownOutside={(e) => e.preventDefault()}
            onInteractOutside={(e) => e.preventDefault()}
          >
            <DialogHeader>
              <DialogTitle>
                {editingNiche ? 'Edit Niche' : 'Create New Niche'}
              </DialogTitle>
              <p className="text-sm text-gray-600">
                Define a new niche market for your blog content strategy.
              </p>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Niche Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="e.g., Health Supplements"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="competition">Competition Level</Label>
                  <Select value={formData.competition_level} onValueChange={(value) => handleInputChange('competition_level', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe this niche market..."
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="keywords">Target Keywords (comma-separated)</Label>
                <Input
                  id="keywords"
                  value={formData.target_keywords}
                  onChange={(e) => handleInputChange('target_keywords', e.target.value)}
                  placeholder="health supplements, protein powder, vitamins"
                />
              </div>

              <div>
                <Label htmlFor="audience">Target Audience</Label>
                <Input
                  id="audience"
                  value={formData.target_audience}
                  onChange={(e) => handleInputChange('target_audience', e.target.value)}
                  placeholder="e.g., Fitness enthusiasts, Health-conscious individuals"
                />
              </div>

              <div>
                <Label htmlFor="themes">Content Themes (comma-separated)</Label>
                <Input
                  id="themes"
                  value={formData.content_themes}
                  onChange={(e) => handleInputChange('content_themes', e.target.value)}
                  placeholder="product reviews, health tips, comparisons"
                />
              </div>

              <div>
                <Label htmlFor="networks">Affiliate Networks (comma-separated)</Label>
                <Input
                  id="networks"
                  value={formData.affiliate_networks}
                  onChange={(e) => handleInputChange('affiliate_networks', e.target.value)}
                  placeholder="Amazon Associates, ClickBank, ShareASale"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="score">Profitability Score (0-100)</Label>
                  <Input
                    id="score"
                    type="number"
                    min="0"
                    max="100"
                    value={formData.profitability_score}
                    onChange={(e) => handleInputChange('profitability_score', parseInt(e.target.value) || 0)}
                  />
                </div>
                <div>
                  <Label htmlFor="strategy">Monetization Strategy</Label>
                  <Textarea
                    id="strategy"
                    value={formData.monetization_strategy}
                    onChange={(e) => handleInputChange('monetization_strategy', e.target.value)}
                    placeholder="Affiliate marketing, sponsored content..."
                    rows={2}
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button type="button" variant="outline" onClick={() => {
                  resetForm();
                  setIsDialogOpen(false);
                }}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-green-600 hover:bg-green-700">
                  {editingNiche ? 'Update Niche' : 'Create Niche'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {activationError && (
        <div className="flex items-center space-x-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <AlertTriangle className="w-5 h-5" />
          <span>{activationError}</span>
        </div>
      )}

      {automationSummary && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase text-gray-500">Active niche</p>
              <div className="flex items-center space-x-2">
                <Rocket className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-semibold">Niche #{automationSummary.niche_id}</h3>
                <span className="flex items-center text-green-700 text-sm">
                  <CheckCircle2 className="w-4 h-4 mr-1" />
                  Automation running
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">Agents: {automationSummary.assigned_agents.join(', ')}</p>
              <p className="text-sm text-gray-700 mt-2">{automationSummary.profitability_insight?.summary}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Activated</p>
              <p className="text-sm font-medium">{new Date(automationSummary.activated_at).toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-2">Tasks seeded: {automationSummary.tasks_seeded?.length || 0}</p>
            </div>
          </div>

          {automationSummary.tasks_seeded?.length > 0 && (
            <div className="mt-3 grid md:grid-cols-2 gap-3">
              {automationSummary.tasks_seeded.slice(0, 4).map((task) => (
                <div key={task.id || task.task_id} className="border border-gray-100 rounded p-3 text-sm">
                  <p className="font-medium capitalize">{task.task_type.replace('_', ' ')}</p>
                  <p className="text-gray-600">Assigned to {task.assigned_agent}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {niches.length === 0 ? (
        <div className="text-center py-12">
          <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-600 mb-2">No niches found</h3>
          <p className="text-gray-500 mb-6">Get started by creating your first niche to organize your products and content.</p>
          <Dialog 
            open={isDialogOpen} 
            onOpenChange={(open) => {
              if (open) {
                setIsDialogOpen(true);
              }
            }}
          >
            <DialogTrigger asChild>
              <Button onClick={() => {
                resetForm();
                setIsDialogOpen(true);
              }} className="bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Niche
              </Button>
            </DialogTrigger>
          </Dialog>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {niches.map((niche) => (
            <div key={niche.id} className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center">
                  <Target className="w-6 h-6 text-blue-600 mr-2" />
                  <h3 className="text-lg font-semibold">{niche.name}</h3>
                </div>
                <div className="flex space-x-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(niche)}
                    className="p-2"
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDelete(niche.id)}
                    className="p-2 text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {niche.description && (
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">{niche.description}</p>
              )}

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Competition</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    niche.competition_level === 'low' ? 'bg-green-100 text-green-800' :
                    niche.competition_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {niche.competition_level}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500 flex items-center">
                    <DollarSign className="w-4 h-4 mr-1" />
                    Profitability
                  </span>
                  <span className="font-medium">{niche.profitability_score}/100</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    Products
                  </span>
                  <span className="font-medium">{niche.products_count || 0}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500 flex items-center">
                    <Users className="w-4 h-4 mr-1" />
                    Articles
                  </span>
                  <span className="font-medium">{niche.articles_count || 0}</span>
                </div>
              </div>

              {/* Pipeline Status */}
              {niche.pipeline_status && niche.pipeline_status !== 'idle' && (
                <div className={`mt-4 p-3 rounded-lg text-sm ${
                  niche.pipeline_status === 'completed' ? 'bg-green-50 border border-green-200' :
                  niche.pipeline_status === 'error' ? 'bg-red-50 border border-red-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <div className="flex items-center space-x-2">
                    {(niche.pipeline_status === 'discovering_products' || niche.pipeline_status === 'generating_articles') && (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    )}
                    {niche.pipeline_status === 'completed' && (
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                    )}
                    {niche.pipeline_status === 'error' && (
                      <AlertCircle className="w-4 h-4 text-red-600" />
                    )}
                    <span className={`font-medium ${
                      niche.pipeline_status === 'completed' ? 'text-green-700' :
                      niche.pipeline_status === 'error' ? 'text-red-700' :
                      'text-blue-700'
                    }`}>
                      {niche.pipeline_status === 'discovering_products' ? 'Discovering Products...' :
                       niche.pipeline_status === 'generating_articles' ? 'Generating Articles...' :
                       niche.pipeline_status === 'completed' ? 'Pipeline Complete' :
                       niche.pipeline_status === 'error' ? 'Pipeline Error' :
                       niche.pipeline_status}
                    </span>
                  </div>
                  {niche.pipeline_message && (
                    <p className="mt-1 text-xs text-gray-600">{niche.pipeline_message}</p>
                  )}
                </div>
              )}

              {/* Run Pipeline Button */}
              {(!niche.pipeline_status || niche.pipeline_status === 'idle' || niche.pipeline_status === 'completed' || niche.pipeline_status === 'error') && (
                <div className="mt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleRunPipeline(niche.id)}
                    className="w-full text-blue-600 border-blue-200 hover:bg-blue-50"
                  >
                    <Rocket className="w-4 h-4 mr-2" />
                    {niche.pipeline_status === 'completed' ? 'Re-run Pipeline' : 
                     niche.pipeline_status === 'error' ? 'Retry Pipeline' : 
                     'Discover Products & Generate Articles'}
                  </Button>
                </div>
              )}

              {niche.target_keywords && niche.target_keywords.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="text-xs text-gray-500 mb-2">Target Keywords:</p>
                  <div className="flex flex-wrap gap-1">
                    {niche.target_keywords.slice(0, 3).map((keyword, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {keyword.trim()}
                      </span>
                    ))}
                    {niche.target_keywords.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                        +{niche.target_keywords.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Niches;
