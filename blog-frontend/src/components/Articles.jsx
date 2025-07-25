import { useState, useEffect } from 'react';
import WordPressPostEditor from './WordPressPostEditor';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Edit, Trash2, Search, RefreshCw, Eye, FileText, Upload, ExternalLink, AlertTriangle, Check, X, Pencil } from 'lucide-react';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { blogApi } from '@/services/api';

const Articles = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [wordpressStatuses, setWordpressStatuses] = useState({});
  const [loadingWordpressStatus, setLoadingWordpressStatus] = useState({});
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [isWordPressEditorOpen, setIsWordPressEditorOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deletingWordPress, setDeletingWordPress] = useState(false);

  useEffect(() => {
    fetchArticles();
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
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Generate New Article
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
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
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
