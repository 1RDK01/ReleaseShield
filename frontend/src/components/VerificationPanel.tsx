'use client'

import { CheckCircle2, XCircle, Clock, Play } from 'lucide-react'
import type { FullState, VerificationCommand } from '@/lib/types'

interface Props {
  state: FullState | null
  onVerify: () => void
  isBusy: boolean
}

function CommandRow({ cmd }: { cmd: VerificationCommand }) {
  const Icon = cmd.passed ? CheckCircle2 : XCircle
  const color = cmd.passed ? '#10b981' : '#ef4444'
  const countStr = cmd.test_count
    ? ` (${cmd.pass_count}/${cmd.test_count})`
    : ''

  return (
    <div>
      <div
        className="flex items-center gap-3 px-4 py-3 border-b"
        style={{ borderColor: '#1e2d45' }}
      >
        <Icon size={16} style={{ color, flexShrink: 0 }} />
        <span className="flex-1 text-sm" style={{ color: '#e2e8f0' }}>
          {cmd.label}{countStr}
        </span>
        <span className="text-xs font-mono" style={{ color: '#64748b' }}>
          {cmd.duration_seconds.toFixed(1)}s
        </span>
        <span
          className="text-xs font-bold px-2 py-0.5 rounded"
          style={{
            color,
            background: `${color}18`,
          }}
        >
          {cmd.passed ? 'PASS' : 'FAIL'}
        </span>
      </div>
      {!cmd.passed && (cmd.stderr || cmd.stdout) && (
        <div
          className="terminal px-4 py-3 text-xs overflow-auto max-h-40"
          style={{ background: '#060b16', color: '#fca5a5' }}
        >
          <pre className="whitespace-pre-wrap">
            {(cmd.stderr || cmd.stdout || '').slice(0, 1500)}
          </pre>
        </div>
      )}
    </div>
  )
}

export function VerificationPanel({ state, onVerify, isBusy }: Props) {
  const vr = state?.verification_result
  const status = state?.workflow_status

  return (
    <div className="space-y-4">
      {status === 'remediated' && !isBusy && (
        <div
          className="rounded-xl p-6 border text-center"
          style={{ background: 'rgba(16,185,129,0.05)', borderColor: 'rgba(16,185,129,0.3)' }}
        >
          <p className="text-sm mb-4" style={{ color: '#94a3b8' }}>
            Remediation complete. Run verification to confirm repository consistency.
          </p>
          <button
            onClick={onVerify}
            className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold mx-auto"
            style={{ background: '#10b981', color: 'white' }}
          >
            <Play size={14} />
            Run Verification
          </button>
        </div>
      )}

      {!vr && status !== 'remediated' && (
        <div
          className="rounded-xl p-8 border text-center"
          style={{ background: '#0f1629', borderColor: '#1e2d45' }}
        >
          <p style={{ color: '#64748b' }}>No verification results yet</p>
        </div>
      )}

      {vr && (
        <div className="space-y-4">
          {/* Summary */}
          <div
            className={`rounded-xl p-5 border ${vr.all_passed ? 'glow-success' : 'glow-danger'}`}
            style={{
              background: vr.all_passed ? 'rgba(16,185,129,0.05)' : 'rgba(239,68,68,0.05)',
              borderColor: vr.all_passed ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
            }}
          >
            <div className="flex items-center gap-3">
              {vr.all_passed ? (
                <CheckCircle2 size={24} style={{ color: '#10b981' }} />
              ) : (
                <XCircle size={24} style={{ color: '#ef4444' }} />
              )}
              <div>
                <div className="font-bold" style={{ color: vr.all_passed ? '#10b981' : '#ef4444' }}>
                  {vr.all_passed ? 'All Checks Passed' : 'Verification Failed'}
                </div>
                <div className="text-xs mt-0.5" style={{ color: '#64748b' }}>
                  {vr.commands.filter(c => c.passed).length} / {vr.commands.length} checks passed
                  {vr.attempt > 1 ? ` (after ${vr.attempt} attempt${vr.attempt > 1 ? 's' : ''})` : ''}
                </div>
              </div>
            </div>
          </div>

          {/* Command results */}
          <div
            className="rounded-xl border overflow-hidden"
            style={{ background: '#0f1629', borderColor: '#1e2d45' }}
          >
            <div className="px-4 py-3 border-b text-xs font-semibold uppercase tracking-wide" 
              style={{ borderColor: '#1e2d45', color: '#64748b' }}>
              Verification Commands
            </div>
            {vr.commands.map((cmd, i) => (
              <CommandRow key={i} cmd={cmd} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
