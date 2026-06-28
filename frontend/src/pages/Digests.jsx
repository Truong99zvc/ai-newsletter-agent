import { useState, useEffect, useCallback } from 'react'
import { Search, ExternalLink, Newspaper } from 'lucide-react'
import { api } from '../api'

const SOURCES = ['all', 'youtube', 'openai', 'anthropic', 'arxiv', 'deepmind', 'huggingface']

export default function Digests() {
  const [digests, setDigests] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [source, setSource] = useState('all')
  const [page, setPage] = useState(0)
  const limit = 15

  const loadDigests = useCallback(async () => {
    setLoading(true)
    try {
      const params = { limit, offset: page * limit }
      if (source !== 'all') params.source = source
      if (search.trim()) params.q = search.trim()
      const data = await api.getDigests(params)
      setDigests(data.items || [])
      setTotal(data.total || 0)
    } catch (e) {
      console.error('Failed to load digests:', e)
    }
    setLoading(false)
  }, [search, source, page])

  useEffect(() => {
    loadDigests()
  }, [loadDigests])

  useEffect(() => {
    setPage(0)
  }, [search, source])

  function getScoreClass(score) {
    if (score == null) return ''
    if (score >= 7) return 'high'
    if (score >= 4) return 'medium'
    return 'low'
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div>
      <div className="page-header">
        <h2>Digests</h2>
        <p>Browse AI-generated summaries from all sources</p>
      </div>

      {/* Search */}
      <div className="search-container">
        <Search size={18} className="search-icon" />
        <input
          type="text"
          className="search-input"
          placeholder="Search digests by title or content..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Source Filters */}
      <div className="filter-row">
        {SOURCES.map(s => (
          <button
            key={s}
            className={`filter-chip ${source === s ? 'active' : ''}`}
            onClick={() => setSource(s)}
          >
            {s === 'all' ? 'All Sources' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Results Count */}
      <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 }}>
        {total} {total === 1 ? 'digest' : 'digests'} found
        {search && ` for "${search}"`}
        {source !== 'all' && ` in ${source}`}
      </p>

      {/* Digest List */}
      {loading ? (
        <div className="digest-list">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="skeleton" style={{ height: 120 }} />)}
        </div>
      ) : digests.length === 0 ? (
        <div className="empty-state">
          <Newspaper size={48} />
          <h3>No digests found</h3>
          <p>{search ? 'Try a different search term' : 'Run the pipeline to generate digests'}</p>
        </div>
      ) : (
        <div className="digest-list">
          {digests.map(digest => (
            <div key={digest.id} className="digest-card">
              <div className="digest-meta">
                <span className={`source-badge ${digest.article_type}`}>
                  {digest.article_type}
                </span>
                {digest.relevance_score != null && (
                  <span className={`score-badge ${getScoreClass(digest.relevance_score)}`}>
                    ★ {digest.relevance_score.toFixed(1)}
                  </span>
                )}
                {digest.rank && (
                  <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                    #{digest.rank}
                  </span>
                )}
                <span style={{ color: 'var(--text-muted)', fontSize: 12, marginLeft: 'auto' }}>
                  {digest.created_at ? new Date(digest.created_at).toLocaleDateString() : ''}
                </span>
              </div>
              <h3>{digest.title}</h3>
              <p className="digest-summary">{digest.summary}</p>
              <a href={digest.url} target="_blank" rel="noopener noreferrer" className="digest-link">
                Read original <ExternalLink size={12} />
              </a>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 24 }}>
          <button
            className="btn btn-ghost"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            Previous
          </button>
          <span style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', fontSize: 14 }}>
            Page {page + 1} of {totalPages}
          </span>
          <button
            className="btn btn-ghost"
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
