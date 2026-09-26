export type WorkflowStatus =
  | 'idle'
  | 'analyzing'
  | 'analyzed'
  | 'remediating'
  | 'remediated'
  | 'verifying'
  | 'verified'
  | 'failed'

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type FileChangeType = 'developer_changed' | 'bob_discovered' | 'bob_remediated' | 'verified'

export interface GitDiffFile {
  path: string
  status: string
  additions: number
  deletions: number
  diff_snippet?: string
}

export interface GitState {
  branch: string
  commit: string
  short_commit: string
  changed_files: GitDiffFile[]
  diff_summary: string
  is_clean: boolean
}

export interface ImpactedFile {
  path: string
  change_type: FileChangeType
  reason: string
  affected_symbols: string[]
  risk_level: Severity
}

export interface Finding {
  id: string
  title: string
  severity: Severity
  source_file: string
  impacted_files: string[]
  description: string
  reasoning: string
  recommended_action: string
  verification_state: string
}

export interface DependencyEdge {
  source: string
  target: string
  relationship: string
}

export interface ImpactGraph {
  source_change: string
  changed_symbols: string[]
  developer_changed_files: string[]
  bob_discovered_files: ImpactedFile[]
  dependency_edges: DependencyEdge[]
  findings: Finding[]
  analysis_timestamp: string
  bob_reasoning: string
}

export interface RemediationFile {
  path: string
  action: string
  description: string
  diff_snippet?: string
}

export interface RemediationResult {
  success: boolean
  files_modified: RemediationFile[]
  attempt: number
  bob_output: string
  timestamp: string
}

export interface VerificationCommand {
  command: string
  return_code: number
  stdout: string
  stderr: string
  duration_seconds: number
  passed: boolean
  label: string
  test_count?: number
  pass_count?: number
}

export interface VerificationResult {
  all_passed: boolean
  commands: VerificationCommand[]
  attempt: number
}

export interface AuditEvent {
  timestamp: string
  level: string
  message: string
  details?: Record<string, unknown>
}

export interface ReleaseMetrics {
  developer_changed_files: number
  bob_discovered_files: number
  files_synchronized: number
  contracts_updated: number
  tests_updated: number
  verification_checks_passed: number
  verification_checks_total: number
  unresolved_findings: number
  is_release_ready: boolean
}

export interface FullState {
  status?: string
  workflow_status?: WorkflowStatus
  git_state?: GitState
  impact_summary?: {
    developer_files: number
    bob_discovered: number
    findings: number
  }
  impact_graph?: ImpactGraph
  remediation_results?: RemediationResult[]
  verification_result?: VerificationResult
  audit_log?: AuditEvent[]
  error?: string
}
