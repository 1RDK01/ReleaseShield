'use client'

import { Shield, GitBranch, Zap, RefreshCw, Play } from 'lucide-react'
import type { WorkflowStatus, FullState } from '@/lib/types'

interface HeaderProps {
  status: WorkflowStatus
  onAnalyze: () => void
  onRemediate: () => void
  onVerify: () => void
  onReset: () => void
  isBusy: boolean
  state: FullState | null
}

const STATUS_CONFIG: Record<WorkflowStatus, { label: string; color: string; bg: string }> = {
  idle: { label: 'READY', color: '#64748b', bg: 'rgba(100,116,139,0.15)' },
  analyzing: { label: 'ANALYZING', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
  analyzed: { label: 'ANALYZED', color: '#3b82f6', bg: 'rgba(59,130,246,0.15)' },
  remediating: { label: 'REMEDIATING', color: '#8b5cf6', bg: 'rgba(139,92,246,0.15)' },
  remediated: { label: 'REMEDIATED', color: '#06b6d4', bg: 'rgba(6,182,212,0.15)' },
  verifying: { label: 'VERIFYING', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)' },
  verified: { label: 'RELEASE READY', color: '#10b981', bg: 'rgba(16,185,129,0.15)' },
  failed: { label: 'FAILED', color: '#ef4444', bg: 'rgba(239,68,68,0.15)' },
}

export function Header({ status, onAnalyze, onRemediate, onVerify, onReset, isBusy, state }: HeaderProps) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.idle
  const hasImpact = !!state?.impact_summary
  const hasRemediation = (state?.remediation_results?.length || 0) > 0
  const isVerified = status === 'verified'

  return (
    <header
      className="px-6 py-4 border-b flex items-center justify-between"
      style={{ background: '#0f1629', borderColor: '#1e2d45' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <Shield size={28} style={{ color: '#3b82f6' }} />
          {isVerified && (
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-green-500" />
          )}
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight" style={{ color: '#e2e8f0' }}>
            ReleaseShield
          </h1>
          <p className="text-xs" style={{ color: '#64748b' }}>
            Know what breaks before you ship.
          </p>
        </div>
      </div>

      {/* Center: Git info */}
      {state?.git_state && (
        <div className="flex items-center gap-4 text-xs" style={{ color: '#64748b' }}>
          <div className="flex items-center gap-1.5">
            <GitBranch size={12} />
            <span>{state.git_state.branch}</span>
          </div>
          <div className="font-mono">{state.git_state.short_commit}</div>
          <div className="flex items-center gap-2">
            <span
              className="px-2 py-0.5 rounded text-xs font-medium"
              style={{ color: '#ef4444', background: 'rgba(239,68,68,0.15)' }}
            >
              {state.git_state.changed_files.length} changed
            </span>
            {state.impact_summary && (
              <span
                className="px-2 py-0.5 rounded text-xs font-medium"
                style={{ color: '#f59e0b', background: 'rgba(245,158,11,0.15)' }}
              >
                +{state.impact_summary.bob_discovered} discovered
              </span>
            )}
          </div>
        </div>
      )}

      {/* Right: Status + Actions */}
      <div className="flex items-center gap-3">
        {/* Status badge */}
        <div
          className="px-3 py-1.5 rounded-full text-xs font-bold tracking-widest flex items-center gap-2"
          style={{ color: cfg.color, background: cfg.bg }}
        >
          {isBusy && (
            <div
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ background: cfg.color }}
            />
          )}
          {cfg.label}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {(status === 'idle' || status === 'failed') && (
            <button
              onClick={onAnalyze}
              disabled={isBusy}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: isBusy ? 'rgba(59,130,246,0.3)' : '#3b82f6',
                color: 'white',
                cursor: isBusy ? 'not-allowed' : 'pointer',
              }}
            >
              <Zap size={14} />
              Analyze Release Impact
            </button>
          )}

          {status === 'analyzed' && (
            <button
              onClick={onRemediate}
              disabled={isBusy}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: isBusy ? 'rgba(139,92,246,0.3)' : '#8b5cf6',
                color: 'white',
                cursor: isBusy ? 'not-allowed' : 'pointer',
              }}
            >
              <Play size={14} />
              Synchronize Repository
            </button>
          )}

          {(status === 'remediated') && (
            <button
              onClick={onVerify}
              disabled={isBusy}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: isBusy ? 'rgba(16,185,129,0.3)' : '#10b981',
                color: 'white',
                cursor: isBusy ? 'not-allowed' : 'pointer',
              }}
            >
              <Play size={14} />
              Run Verification
            </button>
          )}

          <button
            onClick={onReset}
            disabled={isBusy}
            className="p-2 rounded-lg transition-colors"
            style={{ color: '#64748b', background: 'rgba(100,116,139,0.1)' }}
            title="Reset workflow"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>
    </header>
  )
}
