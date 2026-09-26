'use client'

import { useState, useEffect, useCallback } from 'react'
import { Header } from '@/components/Header'
import { ReleaseOverview } from '@/components/ReleaseOverview'
import { ImpactGraph } from '@/components/ImpactGraph'
import { FindingsList } from '@/components/FindingsList'
import { RemediationPanel } from '@/components/RemediationPanel'
import { VerificationPanel } from '@/components/VerificationPanel'
import { AuditLog } from '@/components/AuditLog'
import { EvidenceReport } from '@/components/EvidenceReport'
import { api } from '@/lib/api'
import type { FullState, WorkflowStatus } from '@/lib/types'

// Type-only helper for state merging
type AnyRecord = Record<string, unknown>

type Tab = 'overview' | 'impact' | 'findings' | 'remediation' | 'verification' | 'evidence'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Release Overview' },
  { id: 'impact', label: 'Impact Graph' },
  { id: 'findings', label: 'Findings' },
  { id: 'remediation', label: 'Repository Changes' },
  { id: 'verification', label: 'Verification' },
  { id: 'evidence', label: 'Evidence Report' },
]

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [state, setState] = useState<FullState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchState = useCallback(async () => {
    try {
      const [fullState, eventsData] = await Promise.all([
        api.getState() as Promise<AnyRecord>,
        api.getEvents() as Promise<{ status: string; audit_log: unknown[] }>,
      ])
      setState({
        ...(fullState as AnyRecord),
        audit_log: eventsData.audit_log,
        workflow_status: (eventsData.status || fullState['status']) as WorkflowStatus,
      } as FullState)
    } catch (e) {
      // silently fail polling
    }
  }, [])

  useEffect(() => {
    fetchState()
    const interval = setInterval(fetchState, 2000)
    return () => clearInterval(interval)
  }, [fetchState])

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    try {
      await api.analyze()
      await fetchState()
      setActiveTab('impact')
    } catch (e: any) {
      setError(e.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRemediate = async () => {
    setLoading(true)
    setError(null)
    try {
      await api.remediate()
      await fetchState()
      setActiveTab('remediation')
    } catch (e: any) {
      setError(e.message || 'Remediation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async () => {
    setLoading(true)
    setError(null)
    try {
      await api.verify()
      await fetchState()
      setActiveTab('verification')
    } catch (e: any) {
      setError(e.message || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = async () => {
    try {
      await api.reset()
      setState(null)
      setError(null)
    } catch (e: any) {
      setError(e.message || 'Reset failed')
    }
  }

  const workflowStatus = state?.workflow_status || 'idle'
  const isBusy = loading || ['analyzing', 'remediating', 'verifying'].includes(workflowStatus)

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#0a0e1a' }}>
      <Header
        status={workflowStatus as WorkflowStatus}
        onAnalyze={handleAnalyze}
        onRemediate={handleRemediate}
        onVerify={handleVerify}
        onReset={handleReset}
        isBusy={isBusy}
        state={state}
      />

      {error && (
        <div className="mx-6 mt-3 px-4 py-3 rounded-lg border text-sm animate-slide-in"
          style={{ background: 'rgba(239,68,68,0.1)', borderColor: '#ef4444', color: '#fca5a5' }}>
          ⚠ {error}
        </div>
      )}

      {/* Tabs */}
      <div className="px-6 mt-4 flex gap-1 border-b" style={{ borderColor: '#1e2d45' }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="px-4 py-2 text-sm font-medium transition-colors rounded-t-lg"
            style={{
              color: activeTab === tab.id ? '#e2e8f0' : '#64748b',
              background: activeTab === tab.id ? '#0f1629' : 'transparent',
              borderBottom: activeTab === tab.id ? '2px solid #3b82f6' : '2px solid transparent',
            }}
          >
            {tab.label}
            {tab.id === 'findings' && state?.impact_summary?.findings
              ? <span className="ml-2 px-1.5 py-0.5 rounded-full text-xs" 
                  style={{ background: '#dc2626', color: 'white' }}>
                  {state.impact_summary.findings}
                </span>
              : null}
          </button>
        ))}
      </div>

      {/* Main content */}
      <main className="flex-1 p-6">
        {activeTab === 'overview' && (
          <ReleaseOverview
            state={state}
            onAnalyze={handleAnalyze}
            isBusy={isBusy}
          />
        )}
        {activeTab === 'impact' && (
          <ImpactGraph state={state} />
        )}
        {activeTab === 'findings' && (
          <FindingsList state={state} />
        )}
        {activeTab === 'remediation' && (
          <RemediationPanel
            state={state}
            onRemediate={handleRemediate}
            isBusy={isBusy}
          />
        )}
        {activeTab === 'verification' && (
          <VerificationPanel
            state={state}
            onVerify={handleVerify}
            isBusy={isBusy}
          />
        )}
        {activeTab === 'evidence' && (
          <EvidenceReport state={state} />
        )}
      </main>

      {/* Audit log sidebar */}
      <div className="fixed bottom-4 right-4 w-80 max-h-64">
        <AuditLog events={state?.audit_log || []} />
      </div>
    </div>
  )
}
