import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './components/Dashboard'
import Products from './components/Products'
import Articles from './components/Articles'
import Niches from './components/Niches'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/products" element={<Products />} />
          <Route path="/articles" element={<Articles />} />
          <Route path="/niches" element={<Niches />} />
          {/* Add other routes here as needed */}
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

