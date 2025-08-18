import { useState, useEffect } from 'react';
import WordPressPostEditor from './WordPressPostEditor';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Edit, Trash2, Search, RefreshCw, Eye, FileText, Upload, ExternalLink, AlertTriangle, Check, X, Pencil } from 'lucide-react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { blogApi } from '@/services/api';

const Articles = () => {
  const [articles, setArticles] = useState([]);
  const [niches, setNiches] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [wordpressStatuses, setWordpressStatuses] = useState({});
  const [loadingWordpressStatus, setLoadingWordpressStatus] = useState({});
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [isWordPressEditorOpen, setIsWordPressEditorOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deletingWordPress, setDeletingWordPress] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [viewingArticle, setViewingArticle] = useState(null);
  const [editingArticle, setEditingArticle] = useState(null);
  const [updating, setUpdating] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    status: 'draft',
    product_id: '',
    primary_keywords: '',
    secondary_keywords: '',
    meta_description: '',
    publish_to_wordpress: false
  });

  useEffect(() => {
    fetchArticles();
    fetchProducts();
  }, []);

  // Fetch WordPress status for each article
  useEffect(() => {
    const fetchWordPressStatuses = async () => {
      const statuses = {};
      
      for (const article of articles) {
        if (article.wordpress_post_id) {
          try {
            setLoadingWordpressStatus(prev => ({ ...prev, [article.id]: true }));
            const data = await blogApi.getWordPressStatus(article.id);
            if (data.success) {
              statuses[article.id] = data.status;
            }
          } catch (error) {
            console.error(`Error fetching WordPress status for article ${article.id}:`, error);
            statuses[article.id] = 'error';
          } finally {
            setLoadingWordpressStatus(prev => ({ ...prev, [article.id]: false }));
          }
        }
      }
      
      setWordpressStatuses(statuses);
    };

    if (articles.length > 0) {
      fetchWordPressStatuses();
    }
  }, [articles]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const data = await blogApi.getArticles();
      if (data.success) {
        setArticles(data.articles || []);
      } else {
        console.error('Error fetching articles:', data.error);
      }
    } catch (error) {
      console.error('Error fetching articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      const data = await blogApi.getProducts();
      if (data.success) {
        setProducts(data.products || []);
      } else {
        console.error('Error fetching products:', data.error);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (article.status && article.status.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleDelete = async (articleId) => {
    if (window.confirm('Are you sure you want to delete this article?')) {
      try {
        const data = await blogApi.deleteArticle(articleId);
        if (data.success) {
          fetchArticles(); // Refresh the list
        } else {
          console.error('Error deleting article:', data.error);
        }
      } catch (error) {
        console.error('Error deleting article:', error);
      }
    }
  };

  const handleStatusChange = async (articleId, newStatus) => {
    try {
      const data = await blogApi.updateArticle(articleId, { status: newStatus });
      if (data.success) {
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error updating article status:', data.error);
      }
    } catch (error) {
      console.error('Error updating article status:', error);
    }
  };

  const handlePublishToWordPress = async (articleId) => {
    try {
      const data = await blogApi.publishToWordPress(articleId);
      if (data.success) {
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error publishing to WordPress:', data.error);
      }
    } catch (error) {
      console.error('Error publishing to WordPress:', error);
    }
  };

  const handleEditWordPressPost = (article) => {
    setSelectedArticle(article);
    setIsWordPressEditorOpen(true);
  };

  const handleDeleteWordPressPost = async () => {
    if (!selectedArticle) return;
    
    setDeletingWordPress(true);
    try {
      const data = await blogApi.deleteWordPressPost(selectedArticle.id);
      if (data.success) {
        setIsDeleteDialogOpen(false);
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error deleting WordPress post:', data.error);
      }
    } catch (error) {
      console.error('Error deleting WordPress post:', error);
    } finally {
      setDeletingWordPress(false);
    }
  };

  const openDeleteDialog = (article) => {
    setSelectedArticle(article);
    setIsDeleteDialogOpen(true);
  };

  const handleCreateArticle = async () => {
    setCreating(true);
    try {
      const data = await blogApi.createArticle(formData);
      if (data.success) {
        setIsCreateDialogOpen(false);
        setFormData({
          title: '',
          content: '',
          status: 'draft',
          product_id: '',
          primary_keywords: '',
          secondary_keywords: '',
          meta_description: '',
          publish_to_wordpress: false
        });
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error creating article:', data.error);
      }
    } catch (error) {
      console.error('Error creating article:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleViewArticle = (article) => {
    setViewingArticle(article);
    setIsViewDialogOpen(true);
  };

  const handleEditArticle = (article) => {
    setEditingArticle(article);
    setFormData({
      title: article.title || '',
      content: article.content || '',
      status: article.status || 'draft',
      product_id: article.product_id?.toString() || '',
      primary_keywords: article.primary_keywords || '',
      secondary_keywords: article.secondary_keywords || '',
      meta_description: article.meta_description || '',
      publish_to_wordpress: false
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdateArticle = async () => {
    if (!editingArticle) return;
    
    setUpdating(true);
    try {
      const data = await blogApi.updateArticle(editingArticle.id, formData);
      if (data.success) {
        setIsEditDialogOpen(false);
        setEditingArticle(null);
        setFormData({
          title: '',
          content: '',
          status: 'draft',
          product_id: '',
          primary_keywords: '',
          secondary_keywords: '',
          meta_description: '',
          publish_to_wordpress: false
        });
        fetchArticles(); // Refresh the list
      } else {
        console.error('Error updating article:', data.error);
      }
    } catch (error) {
      console.error('Error updating article:', error);
    } finally {
      setUpdating(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      published: 'default',
      draft: 'secondary',
      scheduled: 'outline'
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  const getWordPressBadge = (article) => {
    if (loadingWordpressStatus[article.id]) {
      return <Badge variant="outline" className="ml-2 bg-slate-100"><RefreshCw className="h-3 w-3 mr-1 animate-spin" />WordPress</Badge>;
    }
    
    if (!article.wordpress_post_id) {
      return <Badge variant="outline" className="ml-2 bg-slate-100"><X className="h-3 w-3 mr-1" />Not on WordPress</Badge>;
    }
    
    const wpStatus = wordpressStatuses[article.id];
    
    if (wpStatus === 'error') {
      return <Badge variant="destructive" className="ml-2"><AlertTriangle className="h-3 w-3 mr-1" />WordPress Error</Badge>;
    }
    
    if (wpStatus === 'publish') {
      return <Badge variant="default" className="ml-2 bg-green-600"><Check className="h-3 w-3 mr-1" />WordPress Published</Badge>;
    }
    
    if (wpStatus === 'draft') {
      return <Badge variant="secondary" className="ml-2"><FileText className="h-3 w-3 mr-1" />WordPress Draft</Badge>;
    }
    
    return <Badge variant="outline" className="ml-2 bg-slate-100">WordPress</Badge>;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
            <h1 className="text-3xl font-bold tracking-tight">Articles</h1>
            <p className="text-muted-foreground">
              Manage your SEO-optimized articles and content.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={fetchArticles}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create New Article
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Article List</CardTitle>
            <CardDescription>All articles in your system.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center py-4">
              <Input
                placeholder="Search articles..."
                value={searchTerm}
                onChange={handleSearch}
                className="max-w-sm"
              />
              <Search className="ml-2 h-4 w-4 text-muted-foreground" />
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Views</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredArticles.length > 0 ? (
                  filteredArticles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell className="font-medium max-w-xs">
                        <div className="truncate">{article.title}</div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(article.status)}
                        {getWordPressBadge(article)}
                      </TableCell>
                      <TableCell>{article.views || 0}</TableCell>
                      <TableCell>${(article.revenue || 0).toFixed(2)}</TableCell>
                      <TableCell>{formatDate(article.created_at)}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Button variant="ghost" size="sm" onClick={() => handleViewArticle(article)} title="View Article">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEditArticle(article)} title="Edit Article">
                            <Edit className="h-4 w-4" />
                          </Button>
                          {article.status === 'draft' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStatusChange(article.id, 'published')}
                            >
                              <FileText className="h-4 w-4" />
                            </Button>
                          )}
                          {!article.wordpress_post_id ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePublishToWordPress(article.id)}
                              title="Publish to WordPress"
                            >
                              <Upload className="h-4 w-4" />
                            </Button>
                          ) : (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(`${article.wordpress_url}`, '_blank')}
                                title="View on WordPress"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditWordPressPost(article)}
                                title="Edit WordPress Post"
                              >
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openDeleteDialog(article)}
                                title="Delete from WordPress"
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(article.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      No articles found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* WordPress Post Editor Dialog */}
    {selectedArticle && (
      <WordPressPostEditor
        article={selectedArticle}
        isOpen={isWordPressEditorOpen}
        onClose={() => setIsWordPressEditorOpen(false)}
        onSuccess={fetchArticles}
      />
    )}

    {/* Create Article Dialog */}
    <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create New Article</DialogTitle>
          <DialogDescription>
            Create a new SEO-optimized article with optional WordPress publishing.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Enter article title..."
              value={formData.title}
              onChange={(e) => handleFormChange('title', e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="product_id">Associated Product</Label>
            <Select value={formData.product_id} onValueChange={(value) => handleFormChange('product_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select a product" />
              </SelectTrigger>
              <SelectContent>
                {products.map((product) => (
                  <SelectItem key={product.id} value={product.id.toString()}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              placeholder="Enter article content..."
              value={formData.content}
              onChange={(e) => handleFormChange('content', e.target.value)}
              rows={8}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="primary_keywords">Primary Keywords</Label>
              <Input
                id="primary_keywords"
                placeholder="keyword1, keyword2, keyword3"
                value={formData.primary_keywords}
                onChange={(e) => handleFormChange('primary_keywords', e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="secondary_keywords">Secondary Keywords</Label>
              <Input
                id="secondary_keywords"
                placeholder="keyword1, keyword2, keyword3"
                value={formData.secondary_keywords}
                onChange={(e) => handleFormChange('secondary_keywords', e.target.value)}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="meta_description">Meta Description</Label>
            <Textarea
              id="meta_description"
              placeholder="SEO meta description..."
              value={formData.meta_description}
              onChange={(e) => handleFormChange('meta_description', e.target.value)}
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="status">Status</Label>
              <Select value={formData.status} onValueChange={(value) => handleFormChange('status', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2 pt-6">
              <input
                type="checkbox"
                id="publish_to_wordpress"
                checked={formData.publish_to_wordpress}
                onChange={(e) => handleFormChange('publish_to_wordpress', e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="publish_to_wordpress">Publish to WordPress</Label>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)} disabled={creating}>
            Cancel
          </Button>
          <Button onClick={handleCreateArticle} disabled={creating || !formData.title || !formData.content || !formData.product_id}>
            {creating ? 'Creating...' : 'Create Article'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* View Article Dialog */}
    <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{viewingArticle?.title}</DialogTitle>
          <DialogDescription>
            Article Details and Content
          </DialogDescription>
        </DialogHeader>
        {viewingArticle && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <strong>Status:</strong> {getStatusBadge(viewingArticle.status)}
              </div>
              <div>
                <strong>Created:</strong> {formatDate(viewingArticle.created_at)}
              </div>
              <div>
                <strong>Views:</strong> {viewingArticle.views || 0}
              </div>
              <div>
                <strong>Revenue:</strong> ${(viewingArticle.revenue || 0).toFixed(2)}
              </div>
            </div>
            {viewingArticle.meta_description && (
              <div>
                <strong>Meta Description:</strong>
                <p className="text-sm text-muted-foreground mt-1">{viewingArticle.meta_description}</p>
              </div>
            )}
            {viewingArticle.primary_keywords && (
              <div>
                <strong>Keywords:</strong>
                <p className="text-sm text-muted-foreground mt-1">{viewingArticle.primary_keywords}</p>
              </div>
            )}
            <div>
              <strong>Content:</strong>
              <div className="mt-2 p-4 border rounded-lg bg-muted/50 max-h-96 overflow-y-auto">
                <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: viewingArticle.content?.replace(/\n/g, '<br>') }} />
              </div>
            </div>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => setIsViewDialogOpen(false)}>
            Close
          </Button>
          {viewingArticle && (
            <Button onClick={() => {
              setIsViewDialogOpen(false);
              handleEditArticle(viewingArticle);
            }}>
              Edit Article
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* Edit Article Dialog */}
    <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Article</DialogTitle>
          <DialogDescription>
            Update your article content and settings.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="edit_title">Title</Label>
            <Input
              id="edit_title"
              placeholder="Enter article title..."
              value={formData.title}
              onChange={(e) => handleFormChange('title', e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="edit_product_id">Associated Product</Label>
            <Select value={formData.product_id} onValueChange={(value) => handleFormChange('product_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select a product" />
              </SelectTrigger>
              <SelectContent>
                {products.map((product) => (
                  <SelectItem key={product.id} value={product.id.toString()}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="edit_content">Content</Label>
            <Textarea
              id="edit_content"
              placeholder="Enter article content..."
              value={formData.content}
              onChange={(e) => handleFormChange('content', e.target.value)}
              rows={8}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="edit_primary_keywords">Primary Keywords</Label>
              <Input
                id="edit_primary_keywords"
                placeholder="keyword1, keyword2, keyword3"
                value={formData.primary_keywords}
                onChange={(e) => handleFormChange('primary_keywords', e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit_secondary_keywords">Secondary Keywords</Label>
              <Input
                id="edit_secondary_keywords"
                placeholder="keyword1, keyword2, keyword3"
                value={formData.secondary_keywords}
                onChange={(e) => handleFormChange('secondary_keywords', e.target.value)}
              />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="edit_meta_description">Meta Description</Label>
            <Textarea
              id="edit_meta_description"
              placeholder="SEO meta description..."
              value={formData.meta_description}
              onChange={(e) => handleFormChange('meta_description', e.target.value)}
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="edit_status">Status</Label>
              <Select value={formData.status} onValueChange={(value) => handleFormChange('status', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2 pt-6">
              <input
                type="checkbox"
                id="edit_publish_to_wordpress"
                checked={formData.publish_to_wordpress}
                onChange={(e) => handleFormChange('publish_to_wordpress', e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="edit_publish_to_wordpress">Update WordPress</Label>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setIsEditDialogOpen(false)} disabled={updating}>
            Cancel
          </Button>
          <Button onClick={handleUpdateArticle} disabled={updating || !formData.title || !formData.content || !formData.product_id}>
            {updating ? 'Updating...' : 'Update Article'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    {/* Delete WordPress Post Confirmation Dialog */}
    <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete WordPress Post</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete this post from WordPress? This action cannot be undone.
            The article will remain in your local database.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deletingWordPress}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteWordPressPost}
            disabled={deletingWordPress}
            className="bg-red-600 hover:bg-red-700"
          >
            {deletingWordPress ? 'Deleting...' : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
};

export default Articles;
