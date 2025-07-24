import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import Products from './components/Products'
import Articles from './components/Articles'
import GenerateArticle from './components/GenerateArticle'
import Analytics from './components/Analytics'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/products" element={<Products />} />
          <Route path="/articles" element={<Articles />} />
          <Route path="/generate" element={<GenerateArticle />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<div className="p-6"><h1 className="text-2xl font-bold">Settings</h1><p>Settings component coming soon...</p></div>} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App


