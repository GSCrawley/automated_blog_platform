import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { AlertCircle, Loader2 } from 'lucide-react';
import { blogApi } from '@/services/api';

const WordPressPostEditor = ({ article, isOpen, onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [metaDescription, setMetaDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (article) {
      setTitle(article.title || '');
      setContent(article.content || '');
      setMetaDescription(article.meta_description || '');
    }
  }, [article]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await blogApi.updateWordPressPost(article.id, {
        title,
        content,
        meta_description: metaDescription
      });

      if (data.success) {
        onSuccess();
        onClose();
      } else {
        setError(data.error || 'Failed to update WordPress post');
      }
    } catch (error) {
      console.error('Error updating WordPress post:', error);
      setError(error.message || 'An error occurred while updating the WordPress post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle>Edit WordPress Post</DialogTitle>
          <DialogDescription>
            Update your post on WordPress. Changes will be reflected immediately on your WordPress site.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          {error && (
            <div className="bg-red-50 p-3 rounded-md flex items-start text-red-600 mb-4">
              <AlertCircle className="h-5 w-5 mr-2 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Post title"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="meta-description">Meta Description</Label>
            <Input
              id="meta-description"
              value={metaDescription}
              onChange={(e) => setMetaDescription(e.target.value)}
              placeholder="Meta description for SEO"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Post content"
              className="min-h-[300px]"
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loading ? 'Updating...' : 'Update WordPress Post'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default WordPressPostEditor;