import { useState, useEffect } from 'react'
import { Play, Clock, FileText, TrendingUp, CheckCircle, XCircle, Loader } from 'lucide-react'
import { api } from '../api'

const PIPELINE_STEPS = ['scrape', 'enrich', 'digest', 'curate', 'deliver']

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [triggerLoading, setTriggerLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [summaryData, historyData] = await Promise.all([
        api.getAnalyticsSummary(24).catch(() => null),
        api.getPipelineHistory(5).catch(() => ({ runs: [] })),
      ])
      if (summaryData) setSummary(summaryData)
      setHistory(historyData.runs || [])
    } catch (e) {
      console.error('Failed to load dashboard data:', e)
    }
    setLoading(false)
  }

  async function handleTriggerPipeline() {
    setTriggerLoading(true)
    try {
      await api.triggerPipeline({ hours: 24, top_n: 10, send_email: true })
      setTimeout(loadData, 2000)
    } catch (e) {
      console.error('Failed to trigger pipeline:', e)
    }
    setTriggerLoading(false)
  }

  function getStatusIcon(status) {
    switch (status) {
      case 'success': return <CheckCircle size={16} style={{ color: 'var(--accent-green)' }} />
      case 'failed': return <XCircle size={16} style={{ color: 'var(--accent-rose)' }} />
      case 'running': return <Loader size={16} style={{ color: 'var(--accent-amber)', animation: 'spin 1s linear infinite' }} />
      default: return <Clock size={16} style={{ color: 'var(--text-muted)' }} />
    }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>Dashboard</h2>
          <p>Loading...</p>
        </div>
        <div className="stats-grid">
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 110 }} />)}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Dashboard</h2>
          <p>Overview of your AI news pipeline</p>
        </div>
        <button className="btn btn-primary" onClick={handleTriggerPipeline} disabled={triggerLoading}>
          {triggerLoading ? <Loader size={16} /> : <Play size={16} />}
          {triggerLoading ? 'Running...' : 'Run Pipeline'}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Articles Today</div>
          <div className="stat-value">{summary?.articles_today ?? 0}</div>
          <div className="stat-subtext">{summary?.total_articles ?? 0} total</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Digests Today</div>
          <div className="stat-value">{summary?.digests_today ?? 0}</div>
          <div className="stat-subtext">{summary?.total_digests ?? 0} total</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Sources Active</div>
          <div className="stat-value">{Object.keys(summary?.source_breakdown ?? {}).length}</div>
          <div className="stat-subtext">6 registered</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Last Run</div>
          <div className="stat-value" style={{ fontSize: 20 }}>
            {summary?.latest_run ? (
              <span className="status-indicator">
                <span className={`status-dot ${summary.latest_run.status}`}></span>
                {summary.latest_run.status}
              </span>
            ) : '—'}
          </div>
          <div className="stat-subtext">
            {summary?.latest_run?.duration_seconds
              ? `${summary.latest_run.duration_seconds.toFixed(1)}s`
              : 'Never run'}
          </div>
        </div>
      </div>

      {/* Source Breakdown */}
      {summary?.source_breakdown && Object.keys(summary.source_breakdown).length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <span className="card-title">Source Breakdown (Last 24h)</span>
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {Object.entries(summary.source_breakdown).map(([source, count]) => (
              <div key={source} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className={`source-badge ${source}`}>{source}</span>
                <span style={{ fontWeight: 700, fontSize: 18 }}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pipeline History */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Pipeline Runs</span>
        </div>
        {history.length === 0 ? (
          <div className="empty-state">
            <Clock size={48} />
            <h3>No pipeline runs yet</h3>
            <p>Click "Run Pipeline" to get started</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {history.map(run => (
              <div key={run.run_id} className="digest-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {getStatusIcon(run.status)}
                    <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{run.status}</span>
                    <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                      {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
                    <span>📥 {run.articles_scraped ?? 0} scraped</span>
                    <span>📝 {run.digests_created ?? 0} digests</span>
                    {run.duration_seconds && <span>⏱ {run.duration_seconds.toFixed(1)}s</span>}
                  </div>
                </div>
                {/* Pipeline Steps */}
                <div className="pipeline-steps" style={{ marginTop: 12 }}>
                  {PIPELINE_STEPS.map(step => {
                    const stepStatus = run.steps_completed?.[step]
                    let cls = ''
                    if (stepStatus === 'success') cls = 'done'
                    else if (run.current_step === step) cls = 'active'
                    return (
                      <div key={step} className={`pipeline-step ${cls}`}>
                        {step}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
