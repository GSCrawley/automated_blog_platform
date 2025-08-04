import React, { useState, useEffect } from 'react';

const ApiTest = () => {
  const [products, setProducts] = useState([]);
  const [articles, setArticles] = useState([]);
  const [niches, setNiches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const testApis = async () => {
      try {
        console.log('Testing API connections...');
        
        // Test Products API
        const productsResponse = await fetch('http://localhost:5000/api/blog/products');
        const productsData = await productsResponse.json();
        console.log('Products API Response:', productsData);
        setProducts(productsData.products || []);

        // Test Articles API
        const articlesResponse = await fetch('http://localhost:5000/api/blog/articles');
        const articlesData = await articlesResponse.json();
        console.log('Articles API Response:', articlesData);
        setArticles(articlesData.articles || []);

        // Test Niches API
        const nichesResponse = await fetch('http://localhost:5000/api/blog/niches');
        const nichesData = await nichesResponse.json();
        console.log('Niches API Response:', nichesData);
        setNiches(nichesData.niches || []);

        setLoading(false);
      } catch (err) {
        console.error('API Test Error:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    testApis();
  }, []);

  if (loading) return <div className="p-4">Loading API test...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">API Test Results</h1>
      
      <div className="space-y-4">
        <div className="border p-4 rounded">
          <h2 className="text-lg font-semibold">Products ({products.length})</h2>
          {products.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {products.map(product => (
                <li key={product.id} className="text-sm">
                  {product.name} - ${product.price}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No products found</p>
          )}
        </div>

        <div className="border p-4 rounded">
          <h2 className="text-lg font-semibold">Articles ({articles.length})</h2>
          {articles.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {articles.map(article => (
                <li key={article.id} className="text-sm">
                  {article.title}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No articles found</p>
          )}
        </div>

        <div className="border p-4 rounded">
          <h2 className="text-lg font-semibold">Niches ({niches.length})</h2>
          {niches.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {niches.map(niche => (
                <li key={niche.id} className="text-sm">
                  {niche.name} - {niche.profitability_score}/100
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No niches found</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiTest;
