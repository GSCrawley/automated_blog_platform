import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, XCircle, Eye, DollarSign, TrendingUp, Users, RefreshCw, AlertTriangle, Info } from 'lucide-react';
import { blogApi } from '@/services/api';

const ProductApproval = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [processingApproval, setProcessingApproval] = useState({});

  useEffect(() => {
    fetchDiscoveredProducts();
  }, []);

  const fetchDiscoveredProducts = async () => {
    setLoading(true);
    try {
      const data = await blogApi.getProducts();
      if (data.success) {
        // Filter to show only discovered products awaiting approval
        const discoveredProducts = data.products?.filter(product => 
          product.status === 'discovered' || product.status === 'pending_approval'
        ) || [];
        setProducts(discoveredProducts);
      } else {
        console.error('Error fetching products:', data.error);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveProduct = async (productId) => {
    setProcessingApproval(prev => ({ ...prev, [productId]: 'approving' }));
    try {
      const data = await blogApi.updateProduct(productId, { status: 'approved' });
      if (data.success) {
        fetchDiscoveredProducts(); // Refresh the list
      } else {
        console.error('Error approving product:', data.error);
      }
    } catch (error) {
      console.error('Error approving product:', error);
    } finally {
      setProcessingApproval(prev => ({ ...prev, [productId]: null }));
    }
  };

  const handleRejectProduct = async (productId) => {
    setProcessingApproval(prev => ({ ...prev, [productId]: 'rejecting' }));
    try {
      const data = await blogApi.updateProduct(productId, { status: 'rejected' });
      if (data.success) {
        fetchDiscoveredProducts(); // Refresh the list
      } else {
        console.error('Error rejecting product:', data.error);
      }
    } catch (error) {
      console.error('Error rejecting product:', error);
    } finally {
      setProcessingApproval(prev => ({ ...prev, [productId]: null }));
    }
  };

  const handleViewDetails = (product) => {
    setSelectedProduct(product);
    setIsDetailDialogOpen(true);
  };

  const getStatusBadge = (status) => {
    const variants = {
      discovered: { variant: 'secondary', label: 'Discovered' },
      pending_approval: { variant: 'outline', label: 'Pending Approval' },
      approved: { variant: 'default', label: 'Approved' },
      rejected: { variant: 'destructive', label: 'Rejected' }
    };
    
    const config = variants[status] || variants.discovered;
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getCommissionBadge = (commissionRate) => {
    if (!commissionRate) return null;
    
    const rate = parseFloat(commissionRate);
    let variant = 'secondary';
    if (rate >= 10) variant = 'default';
    if (rate >= 20) variant = 'destructive';
    
    return <Badge variant={variant}>{rate}% commission</Badge>;
  };

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return `$${parseFloat(price).toFixed(2)}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Product Approval</h1>
          <p className="text-muted-foreground">
            Review and approve discovered products for inclusion in your blog content.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchDiscoveredProducts}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {products.length === 0 ? (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            No products awaiting approval. Products will appear here after niche declaration triggers automated discovery.
          </AlertDescription>
        </Alert>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Discovered Products ({products.length})</CardTitle>
            <CardDescription>
              Products found through automated affiliate program discovery. Review each product and approve those you want to include in your blog content.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Product</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Commission</TableHead>
                  <TableHead>Trend Score</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell className="font-medium max-w-xs">
                      <div className="truncate">{product.name}</div>
                      <div className="text-sm text-muted-foreground truncate">
                        {product.description}
                      </div>
                    </TableCell>
                    <TableCell>{product.category || 'N/A'}</TableCell>
                    <TableCell>{formatPrice(product.price)}</TableCell>
                    <TableCell>
                      {getCommissionBadge(product.commission_rate)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center">
                        <TrendingUp className="h-4 w-4 mr-1 text-green-500" />
                        {product.trend_score || 0}/100
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(product.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => handleViewDetails(product)}
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleApproveProduct(product.id)}
                          disabled={processingApproval[product.id] === 'approving'}
                          title="Approve Product"
                          className="text-green-600 hover:text-green-700"
                        >
                          {processingApproval[product.id] === 'approving' ? (
                            <RefreshCw className="h-4 w-4 animate-spin" />
                          ) : (
                            <CheckCircle className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRejectProduct(product.id)}
                          disabled={processingApproval[product.id] === 'rejecting'}
                          title="Reject Product"
                          className="text-red-600 hover:text-red-700"
                        >
                          {processingApproval[product.id] === 'rejecting' ? (
                            <RefreshCw className="h-4 w-4 animate-spin" />
                          ) : (
                            <XCircle className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Product Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedProduct?.name}</DialogTitle>
            <DialogDescription>
              Product details and affiliate program information
            </DialogDescription>
          </DialogHeader>
          {selectedProduct && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <strong>Category:</strong> {selectedProduct.category || 'N/A'}
                </div>
                <div>
                  <strong>Price:</strong> {formatPrice(selectedProduct.price)}
                </div>
                <div>
                  <strong>Commission Rate:</strong> {selectedProduct.commission_rate || 'N/A'}%
                </div>
                <div>
                  <strong>Trend Score:</strong> {selectedProduct.trend_score || 0}/100
                </div>
                <div>
                  <strong>Search Volume:</strong> {selectedProduct.search_volume || 'N/A'}
                </div>
                <div>
                  <strong>Competition:</strong> {selectedProduct.competition_level || 'N/A'}
                </div>
              </div>
              
              {selectedProduct.description && (
                <div>
                  <strong>Description:</strong>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedProduct.description}
                  </p>
                </div>
              )}
              
              {selectedProduct.affiliate_programs && (
                <div>
                  <strong>Affiliate Programs:</strong>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedProduct.affiliate_programs}
                  </p>
                </div>
              )}
              
              {selectedProduct.primary_keywords && (
                <div>
                  <strong>Target Keywords:</strong>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedProduct.primary_keywords}
                  </p>
                </div>
              )}

              {selectedProduct.source_url && (
                <div>
                  <strong>Source URL:</strong>
                  <a 
                    href={selectedProduct.source_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm"
                  >
                    {selectedProduct.source_url}
                  </a>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDetailDialogOpen(false)}>
              Close
            </Button>
            {selectedProduct && (
              <div className="flex space-x-2">
                <Button
                  onClick={() => {
                    handleRejectProduct(selectedProduct.id);
                    setIsDetailDialogOpen(false);
                  }}
                  variant="destructive"
                  disabled={processingApproval[selectedProduct.id]}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button
                  onClick={() => {
                    handleApproveProduct(selectedProduct.id);
                    setIsDetailDialogOpen(false);
                  }}
                  disabled={processingApproval[selectedProduct.id]}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              </div>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductApproval;
