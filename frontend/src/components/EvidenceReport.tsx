'use client'

import { FileJson, FileText, Download } from 'lucide-react'
import type { FullState } from '@/lib/types'

export function EvidenceReport({ state }: { state: FullState | null }) {
  const vr = state?.verification_result
  const ig = state?.impact_graph
  const rr = state?.remediation_results
  const git = state?.git_state

  const metrics = {
    developer_changed_files: git?.changed_files.length ?? 0,
    bob_discovered_files: ig?.bob_discovered_files.length ?? 0,
    files_synchronized: rr && rr.length > 0 ? rr[rr.length-1].files_modified.length : 0,
    verification_checks_passed: vr ? vr.commands.filter(c => c.passed).length : 0,
    verification_checks_total: vr?.commands.length ?? 0,
    is_release_ready: vr?.all_passed ?? false,
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div
          className="rounded-xl border p-5 flex items-start gap-3"
          style={{ background: '#0f1629', borderColor: '#1e2d45' }}
        >
          <FileJson size={20} style={{ color: '#3b82f6', flexShrink: 0 }} />
          <div>
            <div className="font-medium text-sm" style={{ color: '#e2e8f0' }}>artifacts/impact.json</div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              Structured impact analysis — changed symbols, dependency graph, findings
            </div>
          </div>
        </div>
        <div
          className="rounded-xl border p-5 flex items-start gap-3"
          style={{ background: '#0f1629', borderColor: '#1e2d45' }}
        >
          <FileJson size={20} style={{ color: '#3b82f6', flexShrink: 0 }} />
          <div>
            <div className="font-medium text-sm" style={{ color: '#e2e8f0' }}>artifacts/verification.json</div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              Verification evidence — commands, pass/fail, durations, test counts
            </div>
          </div>
        </div>
        <div
          className="rounded-xl border p-5 flex items-start gap-3 col-span-2"
          style={{ background: '#0f1629', borderColor: '#1e2d45' }}
        >
          <FileText size={20} style={{ color: '#8b5cf6', flexShrink: 0 }} />
          <div>
            <div className="font-medium text-sm" style={{ color: '#e2e8f0' }}>artifacts/release-report.md</div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              Human-readable release report with full analysis, remediation log, and verification results
            </div>
          </div>
        </div>
      </div>

      {/* Release metrics summary */}
      <div
        className="rounded-xl border p-5"
        style={{ background: '#0f1629', borderColor: '#1e2d45' }}
      >
        <h3 className="text-sm font-semibold mb-4" style={{ color: '#94a3b8' }}>
          RELEASE METRICS SUMMARY
        </h3>
        <div className="space-y-2">
          {[
            ['Developer-changed files', metrics.developer_changed_files, '#ef4444'],
            ['Additional impacted files discovered by Bob', metrics.bob_discovered_files, '#f59e0b'],
            ['Files synchronized', metrics.files_synchronized, '#8b5cf6'],
            [`Verification checks passed`, `${metrics.verification_checks_passed}/${metrics.verification_checks_total}`, metrics.is_release_ready ? '#10b981' : '#ef4444'],
          ].map(([label, value, color]) => (
            <div key={String(label)} className="flex justify-between items-center">
              <span className="text-sm" style={{ color: '#64748b' }}>{label}</span>
              <span className="font-mono text-sm font-bold" style={{ color: color as string }}>
                {String(value)}
              </span>
            </div>
          ))}
        </div>

        <div
          className="mt-4 pt-4 border-t text-center text-sm font-bold"
          style={{
            borderColor: '#1e2d45',
            color: metrics.is_release_ready ? '#10b981' : '#64748b',
          }}
        >
          {metrics.is_release_ready ? '✅ RELEASE READY' : 'Workflow incomplete'}
        </div>
      </div>
    </div>
  )
}
