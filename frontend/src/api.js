/**
 * API client for the AI Newsletter Agent backend.
 * Provides typed methods for all API endpoints.
 */

const API_BASE = '/api/v1';

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }
  return response.json();
}

export const api = {
  // Health
  getHealth: () => request('/health'),

  // Pipeline
  triggerPipeline: (params = {}) =>
    request(`${API_BASE}/pipeline/run`, {
      method: 'POST',
      body: JSON.stringify({ hours: 24, top_n: 10, send_email: true, ...params }),
    }),
  getPipelineStatus: (runId) => request(`${API_BASE}/pipeline/status/${runId}`),
  getPipelineHistory: (limit = 20) => request(`${API_BASE}/pipeline/history?limit=${limit}`),

  // Digests
  getDigests: ({ limit = 20, offset = 0, source, q } = {}) => {
    const params = new URLSearchParams({ limit, offset });
    if (source) params.set('source', source);
    if (q) params.set('q', q);
    return request(`${API_BASE}/digests?${params}`);
  },
  getDigest: (id) => request(`${API_BASE}/digests/${encodeURIComponent(id)}`),

  // Sources
  getSources: () => request(`${API_BASE}/sources`),

  // Analytics
  getAnalyticsSummary: (hours = 24) => request(`${API_BASE}/analytics/summary?hours=${hours}`),
};
