import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Wand2, FileText, TrendingUp, Upload } from 'lucide-react';
import { blogApi } from '@/services/api';

const GenerateArticle = () => {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [generatedArticle, setGeneratedArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const data = await blogApi.getProducts();
      if (data.success) {
        setProducts(data.products || []);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoadingProducts(false);
    }
  };

  const generateArticle = async () => {
    if (!selectedProduct) return;

    setLoading(true);
    try {
      const data = await blogApi.generateArticle(parseInt(selectedProduct));
      if (data.success) {
        setGeneratedArticle(data.article);
      } else {
        console.error('Error generating article:', data.error);
        alert('Error generating article: ' + data.error);
      }
    } catch (error) {
      console.error('Error generating article:', error);
      alert('Error generating article. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const publishToWordPress = async () => {
    if (!generatedArticle) return;
    
    try {
      const data = await blogApi.publishToWordPress(generatedArticle.id);
      if (data.success) {
        alert('Article published to WordPress successfully!');
      } else {
        console.error('Error publishing to WordPress:', data.error);
        alert('Error publishing to WordPress: ' + data.error);
      }
    } catch (error) {
      console.error('Error publishing to WordPress:', error);
      alert('Error publishing to WordPress. Please try again.');
    }
  };

  const selectedProductData = products.find(p => p.id === parseInt(selectedProduct));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Generate Article</h1>
        <p className="text-muted-foreground">
          Create SEO-optimized articles for your products using AI.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Product Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Select Product</span>
            </CardTitle>
            <CardDescription>
              Choose a product to generate an article for
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={selectedProduct} onValueChange={setSelectedProduct}>
              <SelectTrigger>
                <SelectValue placeholder={loadingProducts ? "Loading products..." : "Select a product"} />
              </SelectTrigger>
              <SelectContent>
                {products.map((product) => (
                  <SelectItem key={product.id} value={product.id.toString()}>
                    {product.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selectedProductData && (
              <div className="space-y-3 p-4 border rounded-lg bg-muted/50">
                <div>
                  <h3 className="font-medium">{selectedProductData.name}</h3>
                  <p className="text-sm text-muted-foreground">{selectedProductData.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary">{selectedProductData.category}</Badge>
                  <Badge variant="outline">${selectedProductData.price}</Badge>
                  <Badge variant="outline">Score: {selectedProductData.trend_score}</Badge>
                </div>
                <div className="text-sm">
                  <strong>Keywords:</strong> {selectedProductData.primary_keywords?.join(', ') || 'None'}
                </div>
              </div>
            )}

            <Button 
              onClick={generateArticle} 
              disabled={!selectedProduct || loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating Article...
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4 mr-2" />
                  Generate Article
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Article Preview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Generated Article</span>
            </CardTitle>
            <CardDescription>
              Preview and edit your generated content
            </CardDescription>
          </CardHeader>
          <CardContent>
            {generatedArticle ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Title</label>
                  <div className="p-3 border rounded-md bg-muted/50">
                    {generatedArticle.title}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Meta Description</label>
                  <div className="p-3 border rounded-md bg-muted/50 text-sm">
                    {generatedArticle.meta_description}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Content Preview</label>
                  <Textarea
                    value={generatedArticle.content.substring(0, 500) + '...'}
                    readOnly
                    className="min-h-[200px]"
                  />
                </div>

                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <span>Words: {generatedArticle.word_count}</span>
                  <span>SEO Score: {generatedArticle.seo_score}%</span>
                  <span>Readability: {generatedArticle.readability_score}%</span>
                </div>

                <div className="flex space-x-2">
                  <Button variant="outline" size="sm">
                    Edit Article
                  </Button>
                  <Button size="sm" onClick={publishToWordPress}>
                    <Upload className="h-4 w-4 mr-2" />
                    Publish to WordPress
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a product and click "Generate Article" to create content.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GenerateArticle;

