import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { Badge } from './ui/badge'
import { Trash2, Edit, Plus, Target, TrendingUp, Users, DollarSign } from 'lucide-react'

const Niches = () => {
  const [niches, setNiches] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [selectedNiche, setSelectedNiche] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_keywords: '',
    target_audience: '',
    monetization_strategy: '',
    content_themes: '',
    affiliate_networks: '',
    competition_level: 'medium',
    profitability_score: 0
  })

  useEffect(() => {
    fetchNiches()
  }, [])

  const fetchNiches = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/blog/niches')
      const data = await response.json()
      if (data.success) {
        setNiches(data.niches)
      } else {
        console.error('Error fetching niches:', data.error)
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching niches:', error)
      setLoading(false)
    }
  }

  const handleCreateNiche = async () => {
    try {
      const payload = {
        ...formData,
        target_keywords: formData.target_keywords.split(',').map(k => k.trim()).filter(k => k),
        content_themes: formData.content_themes.split(',').map(t => t.trim()).filter(t => t),
        affiliate_networks: formData.affiliate_networks.split(',').map(n => n.trim()).filter(n => n),
        profitability_score: parseFloat(formData.profitability_score) || 0
      }

      const response = await fetch('http://localhost:5000/api/blog/niches', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()
      if (data.success) {
        setNiches([...niches, data.niche])
        setShowCreateDialog(false)
        resetForm()
      } else {
        console.error('Error creating niche:', data.error)
        alert('Error creating niche: ' + data.error)
      }
    } catch (error) {
      console.error('Error creating niche:', error)
      alert('Error creating niche: ' + error.message)
    }
  }

  const handleUpdateNiche = async () => {
    try {
      const payload = {
        ...formData,
        target_keywords: formData.target_keywords.split(',').map(k => k.trim()).filter(k => k),
        content_themes: formData.content_themes.split(',').map(t => t.trim()).filter(t => t),
        affiliate_networks: formData.affiliate_networks.split(',').map(n => n.trim()).filter(n => n),
        profitability_score: parseFloat(formData.profitability_score) || 0
      }

      const response = await fetch(`http://localhost:5000/api/blog/niches/${selectedNiche.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()
      if (data.success) {
        setNiches(niches.map(n => n.id === selectedNiche.id ? data.niche : n))
        setShowEditDialog(false)
        setSelectedNiche(null)
        resetForm()
      } else {
        console.error('Error updating niche:', data.error)
        alert('Error updating niche: ' + data.error)
      }
    } catch (error) {
      console.error('Error updating niche:', error)
      alert('Error updating niche: ' + error.message)
    }
  }

  const handleDeleteNiche = async (nicheId) => {
    if (!confirm('Are you sure you want to delete this niche?')) return

    try {
      const response = await fetch(`http://localhost:5000/api/blog/niches/${nicheId}`, {
        method: 'DELETE'
      })

      const data = await response.json()
      if (data.success) {
        setNiches(niches.filter(n => n.id !== nicheId))
      } else {
        console.error('Error deleting niche:', data.error)
        alert('Error deleting niche: ' + data.error)
      }
    } catch (error) {
      console.error('Error deleting niche:', error)
      alert('Error deleting niche: ' + error.message)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      target_keywords: '',
      target_audience: '',
      monetization_strategy: '',
      content_themes: '',
      affiliate_networks: '',
      competition_level: 'medium',
      profitability_score: 0
    })
  }

  const openEditDialog = (niche) => {
    setSelectedNiche(niche)
    setFormData({
      name: niche.name,
      description: niche.description || '',
      target_keywords: niche.target_keywords.join(', '),
      target_audience: niche.target_audience || '',
      monetization_strategy: niche.monetization_strategy || '',
      content_themes: niche.content_themes.join(', '),
      affiliate_networks: niche.affiliate_networks.join(', '),
      competition_level: niche.competition_level || 'medium',
      profitability_score: niche.profitability_score || 0
    })
    setShowEditDialog(true)
  }

  const getCompetitionColor = (level) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading niches...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Niche Management</h1>
          <p className="text-gray-600 mt-2">Manage your blog niches and target markets</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Add Niche
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Niche</DialogTitle>
              <DialogDescription>
                Define a new niche market for your blog content strategy.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Niche Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., Health Supplements"
                  />
                </div>
                <div>
                  <Label htmlFor="competition">Competition Level</Label>
                  <Select value={formData.competition_level} onValueChange={(value) => setFormData({...formData, competition_level: value})}>
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
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Describe this niche market..."
                />
              </div>
              <div>
                <Label htmlFor="target_keywords">Target Keywords (comma-separated)</Label>
                <Input
                  id="target_keywords"
                  value={formData.target_keywords}
                  onChange={(e) => setFormData({...formData, target_keywords: e.target.value})}
                  placeholder="health supplements, protein powder, vitamins"
                />
              </div>
              <div>
                <Label htmlFor="target_audience">Target Audience</Label>
                <Input
                  id="target_audience"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({...formData, target_audience: e.target.value})}
                  placeholder="e.g., Fitness enthusiasts, Health-conscious individuals"
                />
              </div>
              <div>
                <Label htmlFor="content_themes">Content Themes (comma-separated)</Label>
                <Input
                  id="content_themes"
                  value={formData.content_themes}
                  onChange={(e) => setFormData({...formData, content_themes: e.target.value})}
                  placeholder="product reviews, health tips, comparisons"
                />
              </div>
              <div>
                <Label htmlFor="affiliate_networks">Affiliate Networks (comma-separated)</Label>
                <Input
                  id="affiliate_networks"
                  value={formData.affiliate_networks}
                  onChange={(e) => setFormData({...formData, affiliate_networks: e.target.value})}
                  placeholder="Amazon Associates, ClickBank, ShareASale"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="profitability_score">Profitability Score (0-100)</Label>
                  <Input
                    id="profitability_score"
                    type="number"
                    min="0"
                    max="100"
                    value={formData.profitability_score}
                    onChange={(e) => setFormData({...formData, profitability_score: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="monetization_strategy">Monetization Strategy</Label>
                  <Textarea
                    id="monetization_strategy"
                    value={formData.monetization_strategy}
                    onChange={(e) => setFormData({...formData, monetization_strategy: e.target.value})}
                    placeholder="Affiliate marketing, sponsored content..."
                    className="h-20"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateNiche}>
                Create Niche
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {niches.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Target className="w-16 h-16 text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold mb-2">No niches found</h3>
            <p className="text-gray-600 mb-4">Get started by creating your first niche to organize your products and content.</p>
            <Button onClick={() => setShowCreateDialog(true)} className="bg-green-600 hover:bg-green-700">
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Niche
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {niches.map((niche) => (
            <Card key={niche.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl">{niche.name}</CardTitle>
                    <CardDescription className="mt-2">{niche.description}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditDialog(niche)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteNiche(niche.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Competition</span>
                    <Badge className={getCompetitionColor(niche.competition_level)}>
                      {niche.competition_level}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Profitability</span>
                    <div className="flex items-center">
                      <DollarSign className="w-4 h-4 text-green-600 mr-1" />
                      <span className="font-semibold">{niche.profitability_score}/100</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Products</span>
                    <div className="flex items-center">
                      <TrendingUp className="w-4 h-4 text-blue-600 mr-1" />
                      <span className="font-semibold">{niche.products_count}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Articles</span>
                    <div className="flex items-center">
                      <Users className="w-4 h-4 text-purple-600 mr-1" />
                      <span className="font-semibold">{niche.articles_count}</span>
                    </div>
                  </div>

                  {niche.target_keywords.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-600 block mb-2">Keywords</span>
                      <div className="flex flex-wrap gap-1">
                        {niche.target_keywords.slice(0, 3).map((keyword, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                        {niche.target_keywords.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{niche.target_keywords.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Niche</DialogTitle>
            <DialogDescription>
              Update the niche information and settings.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_name">Niche Name *</Label>
                <Input
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Health Supplements"
                />
              </div>
              <div>
                <Label htmlFor="edit_competition">Competition Level</Label>
                <Select value={formData.competition_level} onValueChange={(value) => setFormData({...formData, competition_level: value})}>
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
              <Label htmlFor="edit_description">Description</Label>
              <Textarea
                id="edit_description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Describe this niche market..."
              />
            </div>
            <div>
              <Label htmlFor="edit_target_keywords">Target Keywords (comma-separated)</Label>
              <Input
                id="edit_target_keywords"
                value={formData.target_keywords}
                onChange={(e) => setFormData({...formData, target_keywords: e.target.value})}
                placeholder="health supplements, protein powder, vitamins"
              />
            </div>
            <div>
              <Label htmlFor="edit_target_audience">Target Audience</Label>
              <Input
                id="edit_target_audience"
                value={formData.target_audience}
                onChange={(e) => setFormData({...formData, target_audience: e.target.value})}
                placeholder="e.g., Fitness enthusiasts, Health-conscious individuals"
              />
            </div>
            <div>
              <Label htmlFor="edit_content_themes">Content Themes (comma-separated)</Label>
              <Input
                id="edit_content_themes"
                value={formData.content_themes}
                onChange={(e) => setFormData({...formData, content_themes: e.target.value})}
                placeholder="product reviews, health tips, comparisons"
              />
            </div>
            <div>
              <Label htmlFor="edit_affiliate_networks">Affiliate Networks (comma-separated)</Label>
              <Input
                id="edit_affiliate_networks"
                value={formData.affiliate_networks}
                onChange={(e) => setFormData({...formData, affiliate_networks: e.target.value})}
                placeholder="Amazon Associates, ClickBank, ShareASale"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_profitability_score">Profitability Score (0-100)</Label>
                <Input
                  id="edit_profitability_score"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.profitability_score}
                  onChange={(e) => setFormData({...formData, profitability_score: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_monetization_strategy">Monetization Strategy</Label>
                <Textarea
                  id="edit_monetization_strategy"
                  value={formData.monetization_strategy}
                  onChange={(e) => setFormData({...formData, monetization_strategy: e.target.value})}
                  placeholder="Affiliate marketing, sponsored content..."
                  className="h-20"
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateNiche}>
              Update Niche
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Niches

