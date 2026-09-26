"""
Evidence artifact generation for release reports.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional
from .models import WorkflowState, ReleaseMetrics
from .config import settings

logger = logging.getLogger("releaseshield.evidence")


def compute_metrics(state: WorkflowState) -> ReleaseMetrics:
    """Compute release readiness metrics from workflow state."""
    dev_files = 0
    bob_files = 0
    synchronized = 0
    contracts_updated = 0
    tests_updated = 0
    checks_passed = 0
    checks_total = 0

    if state.git_state:
        dev_files = len(state.git_state.changed_files)

    if state.impact_graph:
        bob_files = len(state.impact_graph.bob_discovered_files)

    if state.remediation_results:
        last = state.remediation_results[-1]
        synchronized = len(last.files_modified)
        for f in last.files_modified:
            if "schema" in f.path or "types" in f.path or "migration" in f.path:
                contracts_updated += 1
            if "test" in f.path or "fixture" in f.path:
                tests_updated += 1

    if state.verification_result:
        checks_total = len(state.verification_result.commands)
        checks_passed = sum(1 for c in state.verification_result.commands if c.passed)

    unresolved = 0
    if state.impact_graph:
        unresolved = sum(
            1 for f in state.impact_graph.findings
            if f.verification_state == "unverified"
        )

    is_ready = (
        state.verification_result is not None
        and state.verification_result.all_passed
        and checks_total > 0
    )

    return ReleaseMetrics(
        developer_changed_files=dev_files,
        bob_discovered_files=bob_files,
        files_synchronized=synchronized,
        contracts_updated=contracts_updated,
        tests_updated=tests_updated,
        verification_checks_passed=checks_passed,
        verification_checks_total=checks_total,
        unresolved_findings=unresolved,
        is_release_ready=is_ready,
    )


def generate_impact_json(state: WorkflowState, output_dir: str) -> str:
    """Write artifacts/impact.json"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "impact.json")

    data: dict = {
        "generated_at": datetime.utcnow().isoformat(),
        "source_change": None,
        "changed_symbols": [],
        "developer_changed_files": [],
        "bob_discovered_files": [],
        "dependency_relationships": [],
        "findings": [],
    }

    if state.impact_graph:
        ig = state.impact_graph
        data["source_change"] = ig.source_change
        data["changed_symbols"] = ig.changed_symbols
        data["developer_changed_files"] = ig.developer_changed_files
        data["bob_discovered_files"] = [
            {
                "path": f.path,
                "change_type": f.change_type,
                "reason": f.reason,
                "risk_level": f.risk_level,
            }
            for f in ig.bob_discovered_files
        ]
        data["dependency_relationships"] = [
            {"source": e.source, "target": e.target, "relationship": e.relationship}
            for e in ig.dependency_edges
        ]
        data["findings"] = [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "description": f.description,
                "impacted_files": f.impacted_files,
            }
            for f in ig.findings
        ]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def generate_verification_json(state: WorkflowState, output_dir: str) -> str:
    """Write artifacts/verification.json"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "verification.json")

    data: dict = {
        "generated_at": datetime.utcnow().isoformat(),
        "all_passed": False,
        "commands": [],
    }

    if state.verification_result:
        vr = state.verification_result
        data["all_passed"] = vr.all_passed
        data["commands"] = [
            {
                "label": c.label,
                "command": c.command,
                "passed": c.passed,
                "return_code": c.return_code,
                "duration_seconds": c.duration_seconds,
                "test_count": c.test_count,
                "pass_count": c.pass_count,
                "stdout_excerpt": c.stdout[:500],
            }
            for c in vr.commands
        ]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def generate_release_report(state: WorkflowState, output_dir: str) -> str:
    """Write artifacts/release-report.md"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "release-report.md")
    metrics = compute_metrics(state)

    lines = [
        "# ReleaseShield Release Report",
        f"\n**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** {'✅ RELEASE READY' if metrics.is_release_ready else '⚠️ NOT READY'}",
        "",
        "## Proposed Change",
        "",
    ]

    if state.impact_graph:
        lines.append(f"> **{state.impact_graph.source_change}**")
        lines.append("")
        lines.append("**Changed symbols:**")
        for sym in state.impact_graph.changed_symbols:
            lines.append(f"- `{sym}`")
    else:
        lines.append("> No change analyzed yet.")

    lines += [
        "",
        "## Repository Impact",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Developer-changed files | {metrics.developer_changed_files} |",
        f"| Additional files discovered by Bob | {metrics.bob_discovered_files} |",
        f"| Files synchronized | {metrics.files_synchronized} |",
        f"| Contracts updated | {metrics.contracts_updated} |",
        f"| Tests updated | {metrics.tests_updated} |",
        "",
    ]

    if state.impact_graph and state.impact_graph.bob_discovered_files:
        lines.append("## Files Discovered by IBM Bob")
        lines.append("")
        for f in state.impact_graph.bob_discovered_files:
            lines.append(f"### `{f.path}` [{f.risk_level.upper()}]")
            lines.append(f"**Reason:** {f.reason}")
            lines.append("")

    if state.impact_graph and state.impact_graph.findings:
        lines.append("## Findings")
        lines.append("")
        for finding in state.impact_graph.findings:
            lines.append(f"### {finding.title} [{finding.severity.upper()}]")
            lines.append(f"**Description:** {finding.description}")
            lines.append(f"**Impacted:** {', '.join(f'`{f}`' for f in finding.impacted_files)}")
            lines.append(f"**Action:** {finding.recommended_action}")
            lines.append("")

    if state.remediation_results:
        lines.append("## Remediation")
        lines.append("")
        last = state.remediation_results[-1]
        lines.append(f"Bob performed remediation in {len(state.remediation_results)} attempt(s).")
        lines.append("")
        lines.append("**Files modified:**")
        for f in last.files_modified:
            lines.append(f"- `{f.path}` — {f.action}")
        lines.append("")

    if state.verification_result:
        lines.append("## Verification Results")
        lines.append("")
        lines.append("| Check | Result | Duration |")
        lines.append("|-------|--------|----------|")
        for cmd in state.verification_result.commands:
            status = "✅ PASS" if cmd.passed else "❌ FAIL"
            count = f" ({cmd.pass_count}/{cmd.test_count})" if cmd.test_count else ""
            lines.append(f"| {cmd.label}{count} | {status} | {cmd.duration_seconds:.1f}s |")
        lines.append("")

    lines += [
        "## Summary",
        "",
        f"- **Release Ready:** {'Yes' if metrics.is_release_ready else 'No'}",
        f"- **Verification:** {metrics.verification_checks_passed}/{metrics.verification_checks_total} checks passed",
        f"- **Unresolved findings:** {metrics.unresolved_findings}",
        "",
        "---",
        "*Generated by ReleaseShield — Know what breaks before you ship.*",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def generate_all_artifacts(state: WorkflowState) -> dict:
    """Generate all three artifact files."""
    output_dir = settings.ARTIFACTS_DIR
    os.makedirs(output_dir, exist_ok=True)

    paths = {
        "impact_json": generate_impact_json(state, output_dir),
        "verification_json": generate_verification_json(state, output_dir),
        "release_report": generate_release_report(state, output_dir),
    }
    logger.info(f"Generated artifacts: {list(paths.values())}")
    return paths
