import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus, Edit, Trash2, Search, RefreshCw, AlertCircle, Loader2, Package } from 'lucide-react';
import { blogApi } from '@/services/api';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    price: '',
    currency: 'USD',
    trend_score: '',
    search_volume: '',
    competition_level: 'medium',
    affiliate_programs: '',
    primary_keywords: '',
    secondary_keywords: '',
    source_url: '',
    image_url: '',
    niche_id: ''
  });

  useEffect(() => {
    fetchProducts();
    fetchNiches();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await blogApi.getProducts();
      if (data.success) {
        setProducts(data.products || []);
      } else {
        setError('Failed to fetch products: ' + data.error);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
      setError('Error fetching products. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchNiches = async () => {
    try {
      const data = await blogApi.getNiches();
      if (data.success) {
        setNiches(data.niches || []);
      }
    } catch (error) {
      console.error('Error fetching niches:', error);
    }
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (product.category && product.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: '',
      price: '',
      currency: 'USD',
      trend_score: '',
      search_volume: '',
      competition_level: 'medium',
      affiliate_programs: '',
      primary_keywords: '',
      secondary_keywords: '',
      source_url: '',
      image_url: '',
      niche_id: ''
    });
    setError(null);
    setEditingProduct(null);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Product name is required');
      return false;
    }
    if (!formData.category.trim()) {
      setError('Category is required');
      return false;
    }
    if (!formData.price || parseFloat(formData.price) <= 0) {
      setError('Price must be a positive number');
      return false;
    }
    return true;
  };

  const handleCreate = async () => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      const productData = {
        ...formData,
        price: parseFloat(formData.price),
        trend_score: formData.trend_score ? parseFloat(formData.trend_score) : 0,
        search_volume: formData.search_volume ? parseInt(formData.search_volume) : 0,
        affiliate_programs: formData.affiliate_programs ? formData.affiliate_programs.split(',').map(s => s.trim()) : [],
        primary_keywords: formData.primary_keywords ? formData.primary_keywords.split(',').map(s => s.trim()) : [],
        secondary_keywords: formData.secondary_keywords ? formData.secondary_keywords.split(',').map(s => s.trim()) : [],
        niche_id: formData.niche_id ? parseInt(formData.niche_id) : null
      };

      const data = await blogApi.createProduct(productData);
      if (data.success) {
        setIsCreateDialogOpen(false);
        resetForm();
        fetchProducts();
      } else {
        setError(data.error || 'Failed to create product');
      }
    } catch (error) {
      console.error('Error creating product:', error);
      setError('Error creating product. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name || '',
      description: product.description || '',
      category: product.category || '',
      price: product.price?.toString() || '',
      currency: product.currency || 'USD',
      trend_score: product.trend_score?.toString() || '',
      search_volume: product.search_volume?.toString() || '',
      competition_level: product.competition_level || 'medium',
      affiliate_programs: Array.isArray(product.affiliate_programs) ? product.affiliate_programs.join(', ') : '',
      primary_keywords: Array.isArray(product.primary_keywords) ? product.primary_keywords.join(', ') : '',
      secondary_keywords: Array.isArray(product.secondary_keywords) ? product.secondary_keywords.join(', ') : '',
      source_url: product.source_url || '',
      image_url: product.image_url || '',
      niche_id: product.niche_id?.toString() || ''
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdate = async () => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      const productData = {
        ...formData,
        price: parseFloat(formData.price),
        trend_score: formData.trend_score ? parseFloat(formData.trend_score) : 0,
        search_volume: formData.search_volume ? parseInt(formData.search_volume) : 0,
        affiliate_programs: formData.affiliate_programs ? formData.affiliate_programs.split(',').map(s => s.trim()) : [],
        primary_keywords: formData.primary_keywords ? formData.primary_keywords.split(',').map(s => s.trim()) : [],
        secondary_keywords: formData.secondary_keywords ? formData.secondary_keywords.split(',').map(s => s.trim()) : [],
        niche_id: formData.niche_id ? parseInt(formData.niche_id) : null
      };

      const data = await blogApi.updateProduct(editingProduct.id, productData);
      if (data.success) {
        setIsEditDialogOpen(false);
        resetForm();
        fetchProducts();
      } else {
        setError(data.error || 'Failed to update product');
      }
    } catch (error) {
      console.error('Error updating product:', error);
      setError('Error updating product. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
      try {
        const data = await blogApi.deleteProduct(productId);
        if (data.success) {
          fetchProducts();
        } else {
          setError(data.error || 'Failed to delete product');
        }
      } catch (error) {
        console.error('Error deleting product:', error);
        setError('Error deleting product. Please try again.');
      }
    }
  };

  const getCompetitionBadge = (level) => {
    const variants = {
      low: 'default',
      medium: 'secondary',
      high: 'destructive'
    };
    return <Badge variant={variants[level] || 'secondary'}>{level}</Badge>;
  };

  const openCreateDialog = () => {
    resetForm();
    setIsCreateDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Products</h1>
            <p className="text-muted-foreground">
              Manage your high-ticket products for content generation.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={fetchProducts}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm" onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Add New Product
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded-md flex items-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            {error}
            <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setError(null)}>
              ×
            </Button>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Product List</CardTitle>
            <CardDescription>All products in your system.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center py-4">
              <Input
                placeholder="Search products..."
                value={searchTerm}
                onChange={handleSearch}
                className="max-w-sm"
              />
              <Search className="ml-2 h-4 w-4 text-muted-foreground" />
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Competition</TableHead>
                  <TableHead>Niche</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProducts.length > 0 ? (
                  filteredProducts.map((product) => (
                    <TableRow key={product.id}>
                      <TableCell className="font-medium">
                        <div>
                          <div>{product.name}</div>
                          {product.trend_score && (
                            <div className="text-sm text-muted-foreground">
                              Trend Score: {product.trend_score.toFixed(1)}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{product.category}</TableCell>
                      <TableCell>${product.price?.toFixed(2)}</TableCell>
                      <TableCell>{getCompetitionBadge(product.competition_level)}</TableCell>
                      <TableCell>{product.niche_name || '-'}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(product)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(product.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <div className="flex flex-col items-center justify-center text-muted-foreground">
                        <Package className="h-8 w-8 mb-2" />
                        <p>No products found.</p>
                        <Button variant="link" onClick={openCreateDialog} className="mt-2">
                          Create your first product
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Create Product Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Product</DialogTitle>
            <DialogDescription>
              Add a new high-ticket product to your content generation system.
            </DialogDescription>
          </DialogHeader>
          
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded-md flex items-center">
              <AlertCircle className="h-5 w-5 mr-2" />
              {error}
            </div>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="e.g., MacBook Pro M3"
                />
              </div>
              <div>
                <Label htmlFor="category">Category *</Label>
                <Input
                  id="category"
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  placeholder="e.g., Electronics"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Product description..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="price">Price *</Label>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => handleInputChange('price', e.target.value)}
                  placeholder="0.00"
                />
              </div>
              <div>
                <Label htmlFor="currency">Currency</Label>
                <Select value={formData.currency} onValueChange={(value) => handleInputChange('currency', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                  </SelectContent>
                </Select>
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="trend_score">Trend Score (0-100)</Label>
                <Input
                  id="trend_score"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.trend_score}
                  onChange={(e) => handleInputChange('trend_score', e.target.value)}
                  placeholder="85"
                />
              </div>
              <div>
                <Label htmlFor="search_volume">Search Volume</Label>
                <Input
                  id="search_volume"
                  type="number"
                  value={formData.search_volume}
                  onChange={(e) => handleInputChange('search_volume', e.target.value)}
                  placeholder="10000"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="niche">Niche</Label>
              <Select value={formData.niche_id} onValueChange={(value) => handleInputChange('niche_id', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a niche (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {niches.map((niche) => (
                    <SelectItem key={niche.id} value={niche.id.toString()}>
                      {niche.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="primary_keywords">Primary Keywords (comma-separated)</Label>
              <Input
                id="primary_keywords"
                value={formData.primary_keywords}
                onChange={(e) => handleInputChange('primary_keywords', e.target.value)}
                placeholder="macbook pro, apple laptop, professional laptop"
              />
            </div>

            <div>
              <Label htmlFor="affiliate_programs">Affiliate Programs (comma-separated)</Label>
              <Input
                id="affiliate_programs"
                value={formData.affiliate_programs}
                onChange={(e) => handleInputChange('affiliate_programs', e.target.value)}
                placeholder="Amazon Associates, Best Buy Affiliate"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="source_url">Source URL</Label>
                <Input
                  id="source_url"
                  type="url"
                  value={formData.source_url}
                  onChange={(e) => handleInputChange('source_url', e.target.value)}
                  placeholder="https://example.com/product"
                />
              </div>
              <div>
                <Label htmlFor="image_url">Image URL</Label>
                <Input
                  id="image_url"
                  type="url"
                  value={formData.image_url}
                  onChange={(e) => handleInputChange('image_url', e.target.value)}
                  placeholder="https://example.com/image.jpg"
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Create Product
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Product Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Product</DialogTitle>
            <DialogDescription>
              Update the product information.
            </DialogDescription>
          </DialogHeader>
          
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded-md flex items-center">
              <AlertCircle className="h-5 w-5 mr-2" />
              {error}
            </div>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-name">Product Name *</Label>
                <Input
                  id="edit-name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="e.g., MacBook Pro M3"
                />
              </div>
              <div>
                <Label htmlFor="edit-category">Category *</Label>
                <Input
                  id="edit-category"
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  placeholder="e.g., Electronics"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Product description..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="edit-price">Price *</Label>
                <Input
                  id="edit-price"
                  type="number"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => handleInputChange('price', e.target.value)}
                  placeholder="0.00"
                />
              </div>
              <div>
                <Label htmlFor="edit-currency">Currency</Label>
                <Select value={formData.currency} onValueChange={(value) => handleInputChange('currency', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="edit-competition">Competition Level</Label>
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-trend-score">Trend Score (0-100)</Label>
                <Input
                  id="edit-trend-score"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.trend_score}
                  onChange={(e) => handleInputChange('trend_score', e.target.value)}
                  placeholder="85"
                />
              </div>
              <div>
                <Label htmlFor="edit-search-volume">Search Volume</Label>
                <Input
                  id="edit-search-volume"
                  type="number"
                  value={formData.search_volume}
                  onChange={(e) => handleInputChange('search_volume', e.target.value)}
                  placeholder="10000"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit-niche">Niche</Label>
              <Select value={formData.niche_id} onValueChange={(value) => handleInputChange('niche_id', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a niche (optional)" />
                </SelectTrigger>
                <SelectContent>
                  {niches.map((niche) => (
                    <SelectItem key={niche.id} value={niche.id.toString()}>
                      {niche.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="edit-primary-keywords">Primary Keywords (comma-separated)</Label>
              <Input
                id="edit-primary-keywords"
                value={formData.primary_keywords}
                onChange={(e) => handleInputChange('primary_keywords', e.target.value)}
                placeholder="macbook pro, apple laptop, professional laptop"
              />
            </div>

            <div>
              <Label htmlFor="edit-affiliate-programs">Affiliate Programs (comma-separated)</Label>
              <Input
                id="edit-affiliate-programs"
                value={formData.affiliate_programs}
                onChange={(e) => handleInputChange('affiliate_programs', e.target.value)}
                placeholder="Amazon Associates, Best Buy Affiliate"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-source-url">Source URL</Label>
                <Input
                  id="edit-source-url"
                  type="url"
                  value={formData.source_url}
                  onChange={(e) => handleInputChange('source_url', e.target.value)}
                  placeholder="https://example.com/product"
                />
              </div>
              <div>
                <Label htmlFor="edit-image-url">Image URL</Label>
                <Input
                  id="edit-image-url"
                  type="url"
                  value={formData.image_url}
                  onChange={(e) => handleInputChange('image_url', e.target.value)}
                  placeholder="https://example.com/image.jpg"
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={handleUpdate} disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Update Product
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Products;
