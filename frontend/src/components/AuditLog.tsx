'use client'

import type { AuditEvent } from '@/lib/types'

const LEVEL_COLORS: Record<string, string> = {
  info: '#64748b',
  warning: '#f59e0b',
  error: '#ef4444',
}

export function AuditLog({ events }: { events: AuditEvent[] }) {
  if (events.length === 0) return null

  return (
    <div
      className="rounded-lg border overflow-hidden"
      style={{ background: 'rgba(6,11,22,0.97)', borderColor: '#1e2d45' }}
    >
      <div
        className="px-3 py-1.5 border-b flex items-center gap-2"
        style={{ borderColor: '#1e2d45' }}
      >
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <span className="text-xs font-semibold" style={{ color: '#64748b' }}>
          AUDIT LOG
        </span>
      </div>
      <div className="overflow-y-auto max-h-40 terminal px-2 py-1">
        {events.slice(-20).reverse().map((e, i) => (
          <div key={i} className="py-0.5 flex gap-2">
            <span style={{ color: '#374151', flexShrink: 0 }}>{e.timestamp}</span>
            <span style={{ color: LEVEL_COLORS[e.level] || '#64748b' }}>
              {e.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
