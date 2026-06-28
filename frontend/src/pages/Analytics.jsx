import { useState, useEffect } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { api } from '../api'

const SOURCE_COLORS = {
  youtube: '#ff4444',
  openai: '#10b981',
  anthropic: '#f59e0b',
  arxiv: '#06b6d4',
  deepmind: '#3b82f6',
  huggingface: '#fbbf24',
}

export default function Analytics() {
  const [summary, setSummary] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [summaryData, historyData] = await Promise.all([
        api.getAnalyticsSummary(168).catch(() => null),
        api.getPipelineHistory(10).catch(() => ({ runs: [] })),
      ])
      if (summaryData) setSummary(summaryData)
      setHistory(historyData.runs || [])
    } catch (e) {
      console.error('Failed to load analytics:', e)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <h2>Analytics</h2>
          <p>Loading...</p>
        </div>
        <div className="stats-grid">
          {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 300 }} />)}
        </div>
      </div>
    )
  }

  // Prepare source breakdown data for pie chart
  const sourceData = Object.entries(summary?.source_breakdown ?? {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    color: SOURCE_COLORS[name] || '#888',
  }))

  // Prepare pipeline run data for bar chart
  const runData = [...history].reverse().map(run => ({
    date: run.started_at ? new Date(run.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—',
    scraped: run.articles_scraped ?? 0,
    digests: run.digests_created ?? 0,
    duration: run.duration_seconds ?? 0,
  }))

  const customTooltipStyle = {
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border-subtle)',
    borderRadius: '8px',
    padding: '10px 14px',
    color: 'var(--text-primary)',
    fontSize: '13px',
  }

  return (
    <div>
      <div className="page-header">
        <h2>Analytics</h2>
        <p>Insights into your AI news pipeline performance</p>
      </div>

      {/* Overview Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Articles</div>
          <div className="stat-value">{summary?.total_articles ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Digests</div>
          <div className="stat-value">{summary?.total_digests ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pipeline Runs</div>
          <div className="stat-value">{history.length}</div>
          <div className="stat-subtext">
            {history.filter(r => r.status === 'success').length} successful
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Source Distribution */}
        <div className="chart-container">
          <div className="chart-title">Source Distribution</div>
          {sourceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={sourceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={4}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                >
                  {sourceData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={customTooltipStyle} />
                <Legend
                  wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: 40 }}>
              <p>No source data available</p>
            </div>
          )}
        </div>

        {/* Pipeline Performance */}
        <div className="chart-container">
          <div className="chart-title">Pipeline Performance</div>
          {runData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={runData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                  axisLine={{ stroke: 'var(--border-subtle)' }}
                />
                <YAxis
                  tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                  axisLine={{ stroke: 'var(--border-subtle)' }}
                />
                <Tooltip contentStyle={customTooltipStyle} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="scraped" name="Articles Scraped" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                <Bar dataKey="digests" name="Digests Created" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: 40 }}>
              <p>No pipeline run data</p>
            </div>
          )}
        </div>
      </div>

      {/* Pipeline Run Duration */}
      {runData.length > 0 && (
        <div className="chart-container">
          <div className="chart-title">Pipeline Run Duration (seconds)</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={runData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                axisLine={{ stroke: 'var(--border-subtle)' }}
              />
              <YAxis
                tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                axisLine={{ stroke: 'var(--border-subtle)' }}
              />
              <Tooltip contentStyle={customTooltipStyle} />
              <Bar dataKey="duration" name="Duration (s)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
