import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { LayoutDashboard, Newspaper, BarChart3, Settings, Zap } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Digests from './pages/Digests'
import Analytics from './pages/Analytics'
import SettingsPage from './pages/Settings'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        {/* Sidebar Navigation */}
        <aside className="sidebar">
          <div className="sidebar-logo">
            <div className="logo-icon">
              <Zap size={18} color="#fff" />
            </div>
            <h1>AI Newsletter</h1>
          </div>

          <nav className="sidebar-nav">
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <LayoutDashboard size={18} />
              Dashboard
            </NavLink>
            <NavLink to="/digests" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Newspaper size={18} />
              Digests
            </NavLink>
            <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <BarChart3 size={18} />
              Analytics
            </NavLink>
            <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Settings size={18} />
              Settings
            </NavLink>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/digests" element={<Digests />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
