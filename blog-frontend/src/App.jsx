import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import ProductApproval from './components/ProductApproval'
import ArticlesSimple from './components/ArticlesSimple'
import NichesSimple from './components/NichesSimple'
import Settings from './components/Settings'
import ApiTest from './components/ApiTest'
import ProductsSimple from './components/ProductsSimple'
import Analytics from './components/Analytics'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/products" element={<ProductsSimple />} />
          <Route path="/articles" element={<ArticlesSimple />} />
          <Route path="/niches" element={<NichesSimple />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/api-test" element={<ApiTest />} />
          <Route path="/product-approval" element={<ProductApproval />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

