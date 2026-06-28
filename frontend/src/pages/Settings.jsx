import { useState, useEffect } from 'react'
import { Plug, CheckCircle, Info } from 'lucide-react'
import { api } from '../api'

export default function SettingsPage() {
  const [sources, setSources] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSettings()
  }, [])

  async function loadSettings() {
    setLoading(true)
    try {
      const [sourcesData, healthData] = await Promise.all([
        api.getSources().catch(() => ({ sources: [] })),
        api.getHealth().catch(() => null),
      ])
      setSources(sourcesData.sources || [])
      setHealth(healthData)
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>Settings</h2>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>Settings</h2>
        <p>Manage sources, configuration, and system health</p>
      </div>

      {/* System Health */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">System Health</span>
          {health && (
            <span className="status-indicator">
              <span className={`status-dot ${health.status === 'ok' ? 'success' : 'failed'}`}></span>
              {health.status === 'ok' ? 'Healthy' : 'Issues Detected'}
            </span>
          )}
        </div>
        {health ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                Version
              </div>
              <div style={{ fontWeight: 600, fontSize: 16 }}>{health.version}</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                Database
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <CheckCircle size={14} style={{ color: health.database === 'connected' ? 'var(--accent-green)' : 'var(--accent-rose)' }} />
                <span style={{ fontWeight: 600, fontSize: 16, textTransform: 'capitalize' }}>{health.database}</span>
              </div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 4 }}>
                Sources
              </div>
              <div style={{ fontWeight: 600, fontSize: 16 }}>{health.sources_count} registered</div>
            </div>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>Unable to connect to API</p>
        )}
      </div>

      {/* Registered Sources */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Plug size={16} style={{ display: 'inline', marginRight: 8, verticalAlign: 'text-bottom' }} />
            Registered Sources
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{sources.length} sources</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {sources.map(source => (
            <div
              key={source.name}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '14px 16px',
                background: 'rgba(255,255,255,0.02)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className={`source-badge ${source.name}`}>{source.display_name}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{source.type}</span>
              </div>
              <span className="status-indicator">
                <span className="status-dot success"></span>
                Active
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Info Card */}
      <div className="card" style={{ borderColor: 'rgba(124, 58, 237, 0.2)' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <Info size={20} style={{ color: 'var(--accent-primary-light)', marginTop: 2, flexShrink: 0 }} />
          <div>
            <h4 style={{ fontWeight: 600, marginBottom: 6 }}>Plugin Architecture</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6 }}>
              Sources are registered as plugins implementing the <code style={{ background: 'rgba(124,58,237,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 13 }}>BaseScraper</code> interface.
              To add a new source, create a Python class that extends <code style={{ background: 'rgba(124,58,237,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 13 }}>BaseScraper</code> in{' '}
              <code style={{ background: 'rgba(124,58,237,0.1)', padding: '2px 6px', borderRadius: 4, fontSize: 13 }}>app/scrapers/</code> and register it in the registry.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
