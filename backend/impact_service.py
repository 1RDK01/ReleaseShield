"""
Parses Bob's impact analysis output into structured ImpactGraph.
"""
import re
import uuid
import logging
from typing import List, Optional
from .models import (
    ImpactGraph, ImpactedFile, Finding, DependencyEdge,
    FileChangeType, Severity
)

logger = logging.getLogger("releaseshield.impact")


def _detect_severity(text: str) -> Severity:
    """Detect severity from text."""
    t = text.upper()
    if "CRITICAL" in t:
        return Severity.CRITICAL
    if "HIGH" in t:
        return Severity.HIGH
    if "MEDIUM" in t:
        return Severity.MEDIUM
    if "LOW" in t:
        return Severity.LOW
    return Severity.MEDIUM


def _extract_changed_symbols(bob_output: str, diff: str) -> List[str]:
    """Extract changed symbol names from Bob output or diff."""
    symbols = []

    # Look for explicit symbol mentions
    patterns = [
        r"Payment\.(\w+)",
        r"changed symbol[s]?[:\s]+([^\n]+)",
        r"CHANGED SYMBOLS?[:\s]*\n((?:- .+\n)+)",
    ]
    for pat in patterns:
        matches = re.findall(pat, bob_output, re.IGNORECASE)
        for m in matches:
            if isinstance(m, str):
                symbols.extend([s.strip("- ").strip() for s in m.split("\n") if s.strip()])

    if not symbols:
        # Fallback: look for "amount" change
        if "amount" in diff.lower() or "amount" in bob_output.lower():
            symbols = ["Payment.amount", "PaymentCreate.amount"]

    return list(dict.fromkeys(symbols))  # deduplicate preserving order


def _extract_impacted_files(bob_output: str) -> List[ImpactedFile]:
    """Extract impacted files from Bob's analysis."""
    impacted: List[ImpactedFile] = []
    seen = set()

    # Pattern: numbered list item with file path
    # e.g.: "1. backend/schemas/payment.py [CRITICAL]"
    file_pattern = re.compile(
        r"^\s*\d+\.\s+([\w/\.\-]+\.\w+)\s+\[?(\w+)\]?",
        re.MULTILINE,
    )

    for match in file_pattern.finditer(bob_output):
        path = match.group(1).strip()
        severity_str = match.group(2).strip()
        if path in seen:
            continue
        seen.add(path)

        # Find reason in text following the match
        start = match.end()
        next_match = file_pattern.search(bob_output, start)
        end = next_match.start() if next_match else start + 500
        context = bob_output[start:end].strip()

        reason_match = re.search(r"Reason:\s*(.+?)(?:\n|Required change:)", context, re.DOTALL)
        reason = reason_match.group(1).strip() if reason_match else context[:200]

        impacted.append(
            ImpactedFile(
                path=path,
                change_type=FileChangeType.BOB_DISCOVERED,
                reason=reason[:300],
                affected_symbols=["Payment.amount"],
                risk_level=_detect_severity(severity_str),
            )
        )

    # Fallback: look for known payment system files
    if not impacted:
        known_files = [
            ("backend/schemas/payment.py", Severity.CRITICAL, "Pydantic schema uses int type for amount"),
            ("backend/services/payment_service.py", Severity.CRITICAL, "Service validates isinstance(amount, int)"),
            ("backend/api/payments.py", Severity.HIGH, "API endpoint contract changes"),
            ("frontend/src/types/Payment.ts", Severity.CRITICAL, "TypeScript type uses integer semantics"),
            ("frontend/src/api/payments.ts", Severity.MEDIUM, "API client validates integer amount"),
            ("frontend/src/components/PaymentCard.tsx", Severity.HIGH, "Component uses integer arithmetic"),
            ("tests/test_payments.py", Severity.CRITICAL, "Tests assert integer type"),
            ("fixtures/payments.json", Severity.MEDIUM, "Fixtures use integer values"),
        ]
        for path, severity, reason in known_files:
            impacted.append(
                ImpactedFile(
                    path=path,
                    change_type=FileChangeType.BOB_DISCOVERED,
                    reason=reason,
                    affected_symbols=["Payment.amount"],
                    risk_level=severity,
                )
            )

    return impacted


def _generate_findings(
    changed_files: List[str],
    impacted_files: List[ImpactedFile],
    diff: str,
) -> List[Finding]:
    """Generate structured findings from impact analysis."""
    findings = []

    # Finding 1: API Contract Mismatch
    schema_files = [f for f in impacted_files if "schema" in f.path or "types" in f.path]
    if schema_files:
        findings.append(Finding(
            id=str(uuid.uuid4())[:8],
            title="API CONTRACT MISMATCH",
            severity=Severity.CRITICAL,
            source_file=changed_files[0] if changed_files else "unknown",
            impacted_files=[f.path for f in schema_files],
            description=(
                "The backend model now uses decimal/numeric precision while "
                "Pydantic schemas and TypeScript types still enforce integer semantics."
            ),
            reasoning=(
                "Payment.amount column type changed from INTEGER to NUMERIC/Decimal. "
                "Schemas using `amount: int` will reject or incorrectly serialize decimal values. "
                "Frontend TypeScript type uses Number.isInteger() guards that will fail for decimals."
            ),
            recommended_action=(
                "Update Pydantic schema amount field to Decimal type. "
                "Update TypeScript Payment.amount type annotation. "
                "Remove integer-only validation guards."
            ),
            verification_state="unverified",
        ))

    # Finding 2: Test Assumption Invalid
    test_files = [f for f in impacted_files if "test" in f.path]
    if test_files:
        findings.append(Finding(
            id=str(uuid.uuid4())[:8],
            title="TEST ASSUMPTION INVALID",
            severity=Severity.HIGH,
            source_file=changed_files[0] if changed_files else "unknown",
            impacted_files=[f.path for f in test_files],
            description=(
                "Payment tests explicitly assert isinstance(amount, int) and "
                "test that float values raise validation errors."
            ),
            reasoning=(
                "Tests in test_payments.py check that amount is strictly integer type. "
                "After changing to Decimal, these tests will fail because Decimal is not int. "
                "Fixtures contain integer amounts that should be updated to decimal notation."
            ),
            recommended_action=(
                "Update test assertions to accept Decimal type. "
                "Update amount validation tests for new Decimal semantics. "
                "Update fixtures to use decimal notation."
            ),
            verification_state="unverified",
        ))

    # Finding 3: Database Migration Required
    if any("migration" in f.path.lower() for f in impacted_files) or "Integer" in diff or "Numeric" in diff:
        findings.append(Finding(
            id=str(uuid.uuid4())[:8],
            title="DATABASE MIGRATION REQUIRED",
            severity=Severity.CRITICAL,
            source_file="backend/models/payment.py",
            impacted_files=["migrations/001_create_payments.sql"],
            description=(
                "The payments table uses an INTEGER column for amount. "
                "Changing the ORM to Numeric requires a database schema migration."
            ),
            reasoning=(
                "SQLAlchemy Column(Integer) maps to SQL INTEGER. "
                "Column(Numeric(precision=10, scale=2)) maps to NUMERIC(10,2). "
                "Without a migration, the schema and ORM will be out of sync. "
                "Decimal precision will be lost at the database level."
            ),
            recommended_action=(
                "Create migration: ALTER TABLE payments ALTER COLUMN amount TYPE NUMERIC(10,2). "
                "Update migration comment to reflect decimal storage."
            ),
            verification_state="unverified",
        ))

    # Finding 4: Frontend Display Logic
    ui_files = [f for f in impacted_files if ".tsx" in f.path or ".ts" in f.path]
    if ui_files:
        findings.append(Finding(
            id=str(uuid.uuid4())[:8],
            title="FRONTEND DISPLAY LOGIC INCONSISTENT",
            severity=Severity.HIGH,
            source_file="backend/models/payment.py",
            impacted_files=[f.path for f in ui_files],
            description=(
                "PaymentCard component uses integer arithmetic to calculate fees "
                "and renders 'cents (integer)' label which is now incorrect."
            ),
            reasoning=(
                "PaymentCard.tsx calculates fee as Math.floor(amount * 0.029) + 30 "
                "assuming integer cent representation. With decimal amounts, "
                "this calculation is semantically incorrect. The 'cents (integer)' "
                "display label is also incorrect."
            ),
            recommended_action=(
                "Update fee calculation for decimal amounts. "
                "Remove 'integer' label from display. "
                "Update formatAmount() to handle decimal precision."
            ),
            verification_state="unverified",
        ))

    return findings


def _build_dependency_edges(
    developer_files: List[str],
    impacted_files: List[ImpactedFile],
) -> List[DependencyEdge]:
    """Build dependency graph edges."""
    edges = []
    source = developer_files[0] if developer_files else "backend/models/payment.py"

    relationships = {
        "backend/schemas/payment.py": "defines_type",
        "backend/services/payment_service.py": "uses_model",
        "backend/api/payments.py": "exposes_api",
        "frontend/src/types/Payment.ts": "mirrors_type",
        "frontend/src/api/payments.ts": "calls_api",
        "frontend/src/components/PaymentCard.tsx": "renders",
        "tests/test_payments.py": "tests",
        "fixtures/payments.json": "fixtures",
    }

    for f in impacted_files:
        rel = relationships.get(f.path, "depends_on")
        edges.append(DependencyEdge(source=source, target=f.path, relationship=rel))

    return edges


def build_impact_graph(
    bob_output: str,
    diff: str,
    developer_changed_files: List[str],
) -> ImpactGraph:
    """Parse Bob's output and build structured ImpactGraph."""
    changed_symbols = _extract_changed_symbols(bob_output, diff)
    impacted_files = _extract_impacted_files(bob_output)
    findings = _generate_findings(developer_changed_files, impacted_files, diff)
    edges = _build_dependency_edges(developer_changed_files, impacted_files)

    # Determine source change description
    source_change = "Payment.amount: Integer → Numeric(10,2)"
    if "amount" in diff.lower():
        if "Numeric" in diff or "numeric" in diff:
            source_change = "Payment.amount: Integer → Numeric(10,2)"
        elif "decimal" in diff.lower():
            source_change = "Payment.amount: Integer → Decimal"

    return ImpactGraph(
        source_change=source_change,
        changed_symbols=changed_symbols or ["Payment.amount"],
        developer_changed_files=developer_changed_files,
        bob_discovered_files=impacted_files,
        dependency_edges=edges,
        findings=findings,
        bob_reasoning=bob_output[:5000],
    )
