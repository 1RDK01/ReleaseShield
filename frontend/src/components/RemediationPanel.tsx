'use client'

import { GitCommit, Play, CheckCircle2, Clock } from 'lucide-react'
import type { FullState } from '@/lib/types'

interface Props {
  state: FullState | null
  onRemediate: () => void
  isBusy: boolean
}

export function RemediationPanel({ state, onRemediate, isBusy }: Props) {
  const results = state?.remediation_results || []
  const latest = results[results.length - 1]
  const status = state?.workflow_status

  return (
    <div className="space-y-4">
      {status === 'analyzed' && !isBusy && (
        <div
          className="rounded-xl p-6 border text-center animate-pulse-border"
          style={{ background: 'rgba(139,92,246,0.05)', borderColor: 'rgba(139,92,246,0.4)' }}
        >
          <p className="text-sm mb-4" style={{ color: '#94a3b8' }}>
            Bob has identified {state?.impact_summary?.bob_discovered} files to synchronize.
            Click to begin multi-file remediation.
          </p>
          <button
            onClick={onRemediate}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold mx-auto transition-all"
            style={{ background: '#8b5cf6', color: 'white' }}
          >
            <Play size={14} />
            Synchronize Repository
          </button>
        </div>
      )}

      {results.length === 0 && status !== 'analyzed' && (
        <div
          className="rounded-xl p-8 border text-center"
          style={{ background: '#0f1629', borderColor: '#1e2d45' }}
        >
          <p style={{ color: '#64748b' }}>
            No remediation performed yet
          </p>
        </div>
      )}

      {latest && (
        <div className="space-y-3">
          <div className="text-sm font-medium" style={{ color: '#94a3b8' }}>
            Remediation attempt {latest.attempt} — {latest.files_modified.length} files modified
          </div>
          {latest.files_modified.map(f => (
            <div
              key={f.path}
              className="rounded-lg border p-3 flex items-center gap-3"
              style={{ background: '#0f1629', borderColor: '#1e2d45' }}
            >
              <GitCommit size={14} style={{ color: '#8b5cf6', flexShrink: 0 }} />
              <span className="font-mono text-sm flex-1" style={{ color: '#e2e8f0' }}>
                {f.path}
              </span>
              <span
                className="text-xs px-2 py-0.5 rounded"
                style={{ color: '#10b981', background: 'rgba(16,185,129,0.1)' }}
              >
                {f.action.toUpperCase()}
              </span>
            </div>
          ))}

          {latest.bob_output && (
            <div
              className="rounded-lg border p-4 terminal overflow-auto max-h-48"
              style={{ background: '#060b16', borderColor: '#1e2d45', color: '#94a3b8', fontSize: 11 }}
            >
              <div className="text-xs font-bold mb-2" style={{ color: '#3b82f6' }}>
                BOB OUTPUT
              </div>
              <pre className="whitespace-pre-wrap">{latest.bob_output.slice(0, 2000)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
