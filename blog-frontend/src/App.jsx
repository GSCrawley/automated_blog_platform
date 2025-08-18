import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import Products from './components/Products'
import ProductApproval from './components/ProductApproval'
import Articles from './components/Articles'
import Niches from './components/Niches'
import Settings from './components/Settings'
import ApiTest from './components/ApiTest'
import ProductsDebug from './components/ProductsDebug'
import UiTest from './components/UiTest'
import ProductsSimple from './components/ProductsSimple'
import ArticlesSimple from './components/ArticlesSimple'
import NichesSimple from './components/NichesSimple'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/products" element={<ProductApproval />} />
          <Route path="/products-manual" element={<Products />} />
          <Route path="/articles" element={<Articles />} />
          <Route path="/niches" element={<Niches />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/api-test" element={<ApiTest />} />
          <Route path="/products-debug" element={<ProductsDebug />} />
          <Route path="/ui-test" element={<UiTest />} />
          <Route path="/products-simple" element={<ProductsSimple />} />
          {/* Add other routes here as needed */}
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

