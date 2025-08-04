import React, { useState, useEffect } from 'react';
import { blogApi } from '@/services/api';

const ProductsDebug = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      console.log('ProductsDebug: Starting to fetch products...');
      setLoading(true);
      try {
        console.log('ProductsDebug: Calling blogApi.getProducts()...');
        const data = await blogApi.getProducts();
        console.log('ProductsDebug: API Response:', data);
        
        if (data.success) {
          console.log('ProductsDebug: Setting products:', data.products);
          setProducts(data.products);
        } else {
          console.error('ProductsDebug: API returned success=false');
          setError('API returned success=false');
        }
      } catch (err) {
        console.error('ProductsDebug: Error fetching products:', err);
        setError(err.message);
      } finally {
        console.log('ProductsDebug: Finished fetching, setting loading=false');
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  console.log('ProductsDebug: Rendering with state:', { loading, error, productsCount: products.length });

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Products Debug - Loading...</h1>
        <p>Fetching products from API...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Products Debug - Error</h1>
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Products Debug - Success</h1>
      <p className="mb-4">Found {products.length} products:</p>
      
      {products.length > 0 ? (
        <div className="space-y-4">
          {products.map(product => (
            <div key={product.id} className="border p-4 rounded">
              <h3 className="font-semibold">{product.name}</h3>
              <p className="text-gray-600">{product.description}</p>
              <p className="text-green-600 font-bold">${product.price}</p>
              <p className="text-sm text-gray-500">Category: {product.category}</p>
              <p className="text-sm text-gray-500">Niche: {product.niche_name}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No products found in the response.</p>
      )}
    </div>
  );
};

export default ProductsDebug;
