'use client'

import { Zap, Shield, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import type { FullState } from '@/lib/types'

interface Props {
  state: FullState | null
  onAnalyze: () => void
  isBusy: boolean
}

function MetricCard({
  value,
  label,
  sublabel,
  color,
}: {
  value: number | string
  label: string
  sublabel?: string
  color: string
}) {
  return (
    <div
      className="rounded-xl p-5 border"
      style={{ background: '#0f1629', borderColor: '#1e2d45' }}
    >
      <div className="text-3xl font-bold mb-1" style={{ color }}>
        {value}
      </div>
      <div className="text-sm font-medium" style={{ color: '#e2e8f0' }}>
        {label}
      </div>
      {sublabel && (
        <div className="text-xs mt-1" style={{ color: '#64748b' }}>
          {sublabel}
        </div>
      )}
    </div>
  )
}

export function ReleaseOverview({ state, onAnalyze, isBusy }: Props) {
  const impactSummary = state?.impact_summary
  const gitState = state?.git_state
  const vr = state?.verification_result
  const rr = state?.remediation_results
  const status = state?.workflow_status || 'idle'
  const isReady = status === 'verified' && vr?.all_passed

  return (
    <div className="space-y-6">
      {/* Hero banner */}
      <div
        className="rounded-2xl p-8 border relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #0f1629 0%, #0a0e1a 100%)',
          borderColor: isReady ? '#10b981' : '#1e2d45',
        }}
      >
        <div className="relative z-10">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2" style={{ color: '#e2e8f0' }}>
                {isReady ? '✅ RELEASE READY' : 'RELEASE READINESS'}
              </h2>
              <p className="text-sm max-w-xl" style={{ color: '#64748b' }}>
                A Git diff tells you what changed. ReleaseShield uses IBM Bob to determine{' '}
                <span style={{ color: '#3b82f6' }}>what the change means to the rest of your repository.</span>
              </p>

              {gitState && (
                <div className="mt-4 flex items-center gap-6 text-sm">
                  <div>
                    <span style={{ color: '#64748b' }}>Branch: </span>
                    <span className="font-mono" style={{ color: '#e2e8f0' }}>{gitState.branch}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Commit: </span>
                    <span className="font-mono" style={{ color: '#e2e8f0' }}>{gitState.short_commit}</span>
                  </div>
                  {impactSummary && (
                    <div>
                      <span style={{ color: '#64748b' }}>Impact: </span>
                      <span style={{ color: '#f59e0b' }}>
                        {impactSummary.developer_files} dev + {impactSummary.bob_discovered} discovered by Bob
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="text-right">
              {!gitState && !isBusy && (
                <button
                  onClick={onAnalyze}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all glow-accent"
                  style={{ background: '#3b82f6', color: 'white' }}
                >
                  <Zap size={16} />
                  Analyze Release Impact
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Background decoration */}
        <div
          className="absolute top-0 right-0 w-64 h-64 opacity-5 rounded-full"
          style={{ background: isReady ? '#10b981' : '#3b82f6', transform: 'translate(30%, -30%)' }}
        />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          value={gitState?.changed_files.length ?? '—'}
          label="Developer-changed files"
          sublabel="Explicitly in PR"
          color="#ef4444"
        />
        <MetricCard
          value={impactSummary?.bob_discovered ?? '—'}
          label="Discovered by Bob"
          sublabel="Hidden dependencies"
          color="#f59e0b"
        />
        <MetricCard
          value={rr && rr.length > 0 ? rr[rr.length - 1].files_modified.length : '—'}
          label="Files synchronized"
          sublabel="After remediation"
          color="#8b5cf6"
        />
        <MetricCard
          value={vr ? `${vr.commands.filter(c => c.passed).length}/${vr.commands.length}` : '—'}
          label="Verification checks"
          sublabel="Tests + typecheck"
          color={vr?.all_passed ? '#10b981' : '#64748b'}
        />
      </div>

      {/* The Key Insight */}
      {impactSummary && impactSummary.bob_discovered > 0 && (
        <div
          className="rounded-xl p-6 border"
          style={{ background: 'rgba(245,158,11,0.05)', borderColor: 'rgba(245,158,11,0.3)' }}
        >
          <div className="flex items-start gap-4">
            <AlertTriangle size={20} style={{ color: '#f59e0b', flexShrink: 0, marginTop: 2 }} />
            <div>
              <h3 className="font-semibold mb-1" style={{ color: '#f59e0b' }}>
                Bob Discovered Hidden Impact
              </h3>
              <p className="text-sm" style={{ color: '#94a3b8' }}>
                The developer changed{' '}
                <span className="font-bold" style={{ color: '#ef4444' }}>
                  {impactSummary.developer_files} file
                </span>
                . IBM Bob analyzed the repository and found{' '}
                <span className="font-bold" style={{ color: '#f59e0b' }}>
                  {impactSummary.bob_discovered} additional files
                </span>{' '}
                that will break if not updated. These files were{' '}
                <span style={{ color: '#e2e8f0', fontWeight: 600 }}>not included in the pull request.</span>
              </p>
              {impactSummary.findings > 0 && (
                <p className="text-sm mt-2" style={{ color: '#94a3b8' }}>
                  <span className="font-medium" style={{ color: '#dc2626' }}>
                    {impactSummary.findings} findings
                  </span>{' '}
                  identified including API contract mismatches, invalid test assumptions, and required database migrations.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Release ready */}
      {isReady && (
        <div
          className="rounded-xl p-6 border glow-success"
          style={{ background: 'rgba(16,185,129,0.05)', borderColor: 'rgba(16,185,129,0.4)' }}
        >
          <div className="flex items-center gap-3">
            <CheckCircle2 size={24} style={{ color: '#10b981' }} />
            <div>
              <h3 className="font-bold" style={{ color: '#10b981' }}>
                Repository is consistent — release approved
              </h3>
              <p className="text-sm mt-1" style={{ color: '#64748b' }}>
                All {vr?.commands.length} verification checks passed. Impact discovered, remediated, and verified by IBM Bob.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Idle state */}
      {status === 'idle' && (
        <div
          className="rounded-xl p-8 border text-center"
          style={{ background: '#0f1629', borderColor: '#1e2d45' }}
        >
          <Clock size={32} className="mx-auto mb-3" style={{ color: '#1e2d45' }} />
          <p className="text-sm" style={{ color: '#64748b' }}>
            Introduce a change in the demo repository, then click{' '}
            <strong style={{ color: '#3b82f6' }}>Analyze Release Impact</strong> to begin.
          </p>
          <p className="text-xs mt-2" style={{ color: '#374151' }}>
            Run: <code className="terminal" style={{ color: '#94a3b8' }}>python demo/introduce_change.py</code>
          </p>
        </div>
      )}
    </div>
  )
}
