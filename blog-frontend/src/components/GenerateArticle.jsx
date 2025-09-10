import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Wand2, FileText, TrendingUp } from 'lucide-react';
import { blogApi } from '@/services/api';

const GenerateArticle = () => {
    const navigate = useNavigate();
    const [niches, setNiches] = useState([]);
    const [products, setProducts] = useState([]); // Added missing products state
    const [selectedNiche, setSelectedNiche] = useState('');
    const [selectedProduct, setSelectedProduct] = useState('');
    const [generatedArticle, setGeneratedArticle] = useState(null);
    const [loading, setLoading] = useState(false);
    const [loadingProducts, setLoadingProducts] = useState(true);
    const [error, setError] = useState(null);

  useEffect(() => {
    fetchNiches();
    fetchProducts();
  }, []);
  
  const fetchNiches = async () => {
    try {
      const response = await blogApi.getNiches();
      if (response.success) {
        setNiches(response.niches);
      } else {
        setError('Failed to fetch niches');
      }
    } catch (error) {
      console.error('Error fetching niches:', error);
      setError('Error fetching niches');
    }
  };

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
    if (!selectedNiche || !selectedProduct) return;

    setLoading(true);
    setError(null);

    try {
      const data = await blogApi.generateArticle({
        niche_id: selectedNiche,
        product_id: selectedProduct
      });
      
      if (data.success) {
        setGeneratedArticle(data.article); // Set the generated article in state
        alert('Article generated successfully!');
      } else {
        setError(data.error || 'Failed to generate article');
      }
    } catch (error) {
      console.error('Error generating article:', error);
      setError('Error generating article. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditArticle = () => {
    if (generatedArticle) {
      navigate(`/articles/edit/${generatedArticle.id}`);
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

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Product Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Select Product & Niche</span>
            </CardTitle>
            <CardDescription>
              Choose a product and niche to generate an article for
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Niche Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Select Niche</label>
              <Select value={selectedNiche} onValueChange={setSelectedNiche}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a niche" />
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

            {/* Product Selection */}
            <div>
              <label className="text-sm font-medium mb-2 block">Select Product</label>
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
            </div>

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
              disabled={!selectedProduct || !selectedNiche || loading}
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

                <div>
                  <Button variant="outline" size="sm" onClick={handleEditArticle}>
                    Edit & Open Full Article
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

