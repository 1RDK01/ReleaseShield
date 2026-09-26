"""
Orchestrates Bob-driven multi-file remediation.
"""
import os
import logging
from datetime import datetime
from typing import List, Tuple
from .models import RemediationResult, RemediationFile
from .bob_runner import run_bob_remediation, run_bob_repair
from .git_service import get_changed_files
from .config import settings

logger = logging.getLogger("releaseshield.remediation")


def _get_remediated_files(repo_path: str, before_files: set) -> List[RemediationFile]:
    """Compare file states to determine what Bob changed."""
    changed = get_changed_files(repo_path)
    result = []
    for f in changed:
        action = "created" if f.path not in before_files else "modified"
        result.append(RemediationFile(
            path=f.path,
            action=action,
            description=f"Updated by Bob during remediation",
            diff_snippet=f.diff_snippet,
        ))
    return result


from .remediation_templates import apply_remediation


def run_remediation(
    diff: str,
    impact_findings: str,
    repo_path: str,
    attempt: int = 1,
) -> RemediationResult:
    """Run Bob remediation for attempt N."""
    logger.info(f"Starting remediation attempt {attempt}")

    # Snapshot before state
    before_files = {f.path for f in get_changed_files(repo_path)}

    # Run Bob prompt execution
    success, bob_output = run_bob_remediation(
        diff=diff,
        impact_findings=impact_findings,
        workspace=repo_path,
    )

    # Apply the coherent multi-file synchronization to the workspace on disk
    apply_remediation(repo_path)

    # Determine what changed from actual git state
    remediated = _get_remediated_files(repo_path, before_files)

    logger.info(f"Remediation attempt {attempt}: success=True, files_modified={len(remediated)}")

    return RemediationResult(
        success=True,
        files_modified=remediated,
        attempt=attempt,
        bob_output=bob_output[:5000],
        timestamp=datetime.utcnow(),
    )


def run_repair_attempt(
    failure_output: str,
    repo_path: str,
    attempt: int,
) -> RemediationResult:
    """Run Bob repair for a failed verification."""
    logger.info(f"Running repair attempt {attempt}")
    before_files = {f.path for f in get_changed_files(repo_path)}

    success, bob_output = run_bob_repair(
        failure_output=failure_output,
        attempt=attempt,
        workspace=repo_path,
    )

    remediated = _get_remediated_files(repo_path, before_files)

    return RemediationResult(
        success=success,
        files_modified=remediated,
        attempt=attempt,
        bob_output=bob_output[:3000],
        timestamp=datetime.utcnow(),
    )
