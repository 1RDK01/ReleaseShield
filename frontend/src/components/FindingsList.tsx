'use client'

import { AlertOctagon, AlertTriangle, Info } from 'lucide-react'
import type { FullState, Finding, Severity } from '@/lib/types'

const SEVERITY_ICONS: Record<Severity, typeof AlertOctagon> = {
  critical: AlertOctagon,
  high: AlertTriangle,
  medium: AlertTriangle,
  low: Info,
  info: Info,
}

const SEVERITY_COLORS: Record<Severity, { text: string; bg: string; border: string }> = {
  critical: { text: '#dc2626', bg: 'rgba(220,38,38,0.07)', border: 'rgba(220,38,38,0.3)' },
  high: { text: '#ef4444', bg: 'rgba(239,68,68,0.07)', border: 'rgba(239,68,68,0.3)' },
  medium: { text: '#f59e0b', bg: 'rgba(245,158,11,0.07)', border: 'rgba(245,158,11,0.3)' },
  low: { text: '#3b82f6', bg: 'rgba(59,130,246,0.07)', border: 'rgba(59,130,246,0.3)' },
  info: { text: '#64748b', bg: 'rgba(100,116,139,0.07)', border: 'rgba(100,116,139,0.3)' },
}

function FindingCard({ finding }: { finding: Finding }) {
  const cfg = SEVERITY_COLORS[finding.severity]
  const Icon = SEVERITY_ICONS[finding.severity]

  return (
    <div className="rounded-xl border p-5" style={{ background: cfg.bg, borderColor: cfg.border }}>
      <div className="flex items-start gap-3 mb-3">
        <Icon size={18} style={{ color: cfg.text, flexShrink: 0, marginTop: 2 }} />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-sm" style={{ color: cfg.text }}>
              {finding.title}
            </h3>
            <span
              className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ color: cfg.text, background: `${cfg.text}20` }}
            >
              {finding.severity.toUpperCase()}
            </span>
          </div>
          <p className="text-sm mt-1.5" style={{ color: '#cbd5e1' }}>
            {finding.description}
          </p>
        </div>
      </div>

      <div className="space-y-2 ml-7">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#64748b' }}>
            Reasoning
          </span>
          <p className="text-xs mt-1" style={{ color: '#94a3b8' }}>
            {finding.reasoning}
          </p>
        </div>

        <div>
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#64748b' }}>
            Impacted files
          </span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {finding.impacted_files.map(f => (
              <span
                key={f}
                className="font-mono text-xs px-2 py-0.5 rounded"
                style={{ background: 'rgba(255,255,255,0.05)', color: '#e2e8f0' }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>

        <div>
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#64748b' }}>
            Recommended action
          </span>
          <p className="text-xs mt-1" style={{ color: '#a5b4fc' }}>
            {finding.recommended_action}
          </p>
        </div>
      </div>
    </div>
  )
}

export function FindingsList({ state }: { state: FullState | null }) {
  const findings = state?.impact_graph?.findings || []

  if (findings.length === 0) {
    return (
      <div
        className="rounded-xl p-8 border text-center"
        style={{ background: '#0f1629', borderColor: '#1e2d45' }}
      >
        <p style={{ color: '#64748b' }}>No findings yet — run analysis first</p>
      </div>
    )
  }

  const criticalCount = findings.filter(f => f.severity === 'critical').length
  const highCount = findings.filter(f => f.severity === 'high').length

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm">
        {criticalCount > 0 && (
          <span style={{ color: '#dc2626' }}>{criticalCount} Critical</span>
        )}
        {highCount > 0 && (
          <span style={{ color: '#ef4444' }}>{highCount} High</span>
        )}
        <span style={{ color: '#64748b' }}>{findings.length} total findings</span>
      </div>
      {findings.map(f => (
        <FindingCard key={f.id} finding={f} />
      ))}
    </div>
  )
}
