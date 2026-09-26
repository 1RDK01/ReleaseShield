const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  analyze: () => req<{ status: string }>('/api/analyze', { method: 'POST' }),
  getImpact: () => req<unknown>('/api/impact'),
  remediate: () => req<{ status: string }>('/api/remediate', { method: 'POST' }),
  verify: () => req<{ status: string }>('/api/verify', { method: 'POST' }),
  getReport: () => req<unknown>('/api/report'),
  getEvents: () => req<{ status: string; audit_log: unknown[] }>('/api/events'),
  getState: () => req<unknown>('/api/state'),
  reset: () => req<{ status: string }>('/api/reset', { method: 'POST' }),
}
