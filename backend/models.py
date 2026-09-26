"""
Pydantic response models for ReleaseShield API.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FileChangeType(str, Enum):
    DEVELOPER_CHANGED = "developer_changed"
    BOB_DISCOVERED = "bob_discovered"
    BOB_REMEDIATED = "bob_remediated"
    VERIFIED = "verified"


class WorkflowStatus(str, Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    REMEDIATING = "remediating"
    REMEDIATED = "remediated"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    FAILED = "failed"


class GitDiffFile(BaseModel):
    path: str
    status: str  # modified, added, deleted
    additions: int = 0
    deletions: int = 0
    diff_snippet: Optional[str] = None


class GitState(BaseModel):
    branch: str
    commit: str
    short_commit: str
    changed_files: List[GitDiffFile]
    diff_summary: str
    is_clean: bool


class ImpactedFile(BaseModel):
    path: str
    change_type: FileChangeType
    reason: str
    affected_symbols: List[str] = Field(default_factory=list)
    risk_level: Severity = Severity.MEDIUM


class Finding(BaseModel):
    id: str
    title: str
    severity: Severity
    source_file: str
    impacted_files: List[str]
    description: str
    reasoning: str
    recommended_action: str
    verification_state: str = "unverified"


class DependencyEdge(BaseModel):
    source: str
    target: str
    relationship: str  # "imports", "uses_type", "tests", "documents", etc.


class ImpactGraph(BaseModel):
    source_change: str
    changed_symbols: List[str]
    developer_changed_files: List[str]
    bob_discovered_files: List[ImpactedFile]
    dependency_edges: List[DependencyEdge]
    findings: List[Finding]
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    bob_reasoning: str = ""


class RemediationFile(BaseModel):
    path: str
    action: str  # "modified", "created", "no_change"
    description: str
    diff_snippet: Optional[str] = None


class RemediationResult(BaseModel):
    success: bool
    files_modified: List[RemediationFile]
    attempt: int
    bob_output: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VerificationCommand(BaseModel):
    command: str
    return_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    passed: bool
    label: str
    test_count: Optional[int] = None
    pass_count: Optional[int] = None


class VerificationResult(BaseModel):
    all_passed: bool
    commands: List[VerificationCommand]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attempt: int = 1


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "info"  # info, warning, error
    message: str
    details: Optional[Dict[str, Any]] = None


class WorkflowState(BaseModel):
    status: WorkflowStatus = WorkflowStatus.IDLE
    git_state: Optional[GitState] = None
    impact_graph: Optional[ImpactGraph] = None
    remediation_results: List[RemediationResult] = Field(default_factory=list)
    verification_result: Optional[VerificationResult] = None
    audit_log: List[AuditEvent] = Field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ReleaseMetrics(BaseModel):
    developer_changed_files: int = 0
    bob_discovered_files: int = 0
    files_synchronized: int = 0
    contracts_updated: int = 0
    tests_updated: int = 0
    verification_checks_passed: int = 0
    verification_checks_total: int = 0
    unresolved_findings: int = 0
    is_release_ready: bool = False
