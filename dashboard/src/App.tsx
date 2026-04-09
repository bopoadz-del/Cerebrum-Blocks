import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Key, 
  BarChart3, 
  CreditCard, 
  Settings as SettingsIcon,
  Brain
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import APIKeys from './pages/APIKeys'
import Usage from './pages/Usage'
import Billing from './pages/Billing'
import Settings from './pages/Settings'
import './App.css'

function NavLink({ to, icon: Icon, children }: { to: string; icon: React.ElementType; children: React.ReactNode }) {
  const location = useLocation()
  const active = location.pathname === to
  
  return (
    <Link 
      to={to} 
      className={`nav-link ${active ? 'active' : ''}`}
    >
      <Icon size={20} />
      <span>{children}</span>
    </Link>
  )
}

function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <Brain size={28} />
          <span>Cerebrum</span>
        </div>
        
        <nav className="nav">
          <NavLink to="/" icon={LayoutDashboard}>Overview</NavLink>
          <NavLink to="/keys" icon={Key}>API Keys</NavLink>
          <NavLink to="/usage" icon={BarChart3}>Usage</NavLink>
          <NavLink to="/billing" icon={CreditCard}>Billing</NavLink>
        </nav>
        
        <div className="sidebar-footer">
          <NavLink to="/settings" icon={SettingsIcon}>Settings</NavLink>
        </div>
      </aside>
      
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/keys" element={<APIKeys />} />
          <Route path="/usage" element={<Usage />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
