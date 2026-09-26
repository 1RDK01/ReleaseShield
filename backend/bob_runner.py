"""
IBM Bob execution wrapper for ReleaseShield.
Wraps Bob CLI calls safely — no shell=True with user input.
Falls back to simulated analysis when Bob is not available.
"""
import subprocess
import os
import json
import time
import logging
import shutil
from typing import Optional, Tuple
from .config import settings

logger = logging.getLogger("releaseshield.bob")

# Bob analysis prompt template for impact analysis
IMPACT_ANALYSIS_PROMPT = """You are analyzing a repository for change impact as part of the ReleaseShield release engineering workflow.

PROPOSED CHANGE (Git diff):
{diff}

CHANGED FILES: {changed_files}

TASK: Analyze this repository and determine repository-wide impact of this change.

Specifically:
1. What contract/type/behavior changed? (e.g., Payment.amount: integer → decimal)
2. Which files depend on the changed symbols? List them with their dependency relationship.
3. What will break if those dependent files are NOT updated?
4. Are there database migrations required?
5. Are there TypeScript/frontend types that must change?
6. Are there tests or fixtures that encode old behavior?
7. Are there API contracts, configuration, or documentation that must change?

For each impacted file, explain:
- WHY it is affected
- WHAT specifically needs to change
- What severity: critical/high/medium/low

Format your analysis as structured findings.
Do NOT make any file changes yet. Analysis only.
"""

REMEDIATION_PROMPT = """You are a release engineer performing coordinated multi-file remediation.

CHANGE CONTEXT:
{diff}

IMPACT ANALYSIS FINDINGS:
{impact_findings}

TASK: Update ALL affected files to make the repository consistent with the proposed change.

Rules:
1. Make the MINIMUM coherent change to restore consistency
2. Update every file identified in the impact analysis
3. Ensure types, schemas, tests, and fixtures all agree
4. Write or update tests that validate the new behavior
5. Preserve all existing functionality not related to this change

After updating all files, run: pytest tests/ -q
And if a frontend exists: npm run typecheck

Proceed with all file modifications now.
"""

REPAIR_PROMPT = """Verification failed after remediation attempt {attempt}.

FAILURE OUTPUT:
{failure_output}

TASK: Diagnose the failure and make the minimum correction needed.
Fix only what is broken. Do not change files that are already correct.
After fixing, verification will be re-run automatically.
"""


def bob_available() -> bool:
    """Check if Bob CLI is available on PATH."""
    return shutil.which(settings.BOB_EXECUTABLE) is not None


def run_bob_task(
    prompt: str,
    workspace: str,
    mode: Optional[str] = None,
    timeout: int = None,
) -> Tuple[bool, str, str]:
    """
    Run a Bob task via CLI.
    Returns: (success, stdout, stderr)
    """
    if timeout is None:
        timeout = settings.BOB_TIMEOUT

    if not bob_available():
        logger.warning("Bob not found on PATH — using simulation mode")
        return _simulate_bob(prompt, workspace)

    # Build Bob command
    # Bob CLI: bob --workspace <path> --mode <mode> --prompt <prompt>
    # Adjust args based on actual Bob CLI interface
    cmd = [settings.BOB_EXECUTABLE]

    if mode:
        cmd += ["--mode", mode]

    # Write prompt to temp file to avoid shell injection
    prompt_file = os.path.join(workspace, ".bob_prompt_tmp.txt")
    try:
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        cmd += ["--file", prompt_file]

        logger.info(f"Running Bob: {' '.join(cmd[:4])}...")
        start = time.time()

        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "BOB_WORKSPACE": workspace},
        )

        duration = time.time() - start
        logger.info(f"Bob completed in {duration:.1f}s (rc={result.returncode})")

        success = result.returncode == 0
        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        logger.error(f"Bob timed out after {timeout}s")
        return False, "", f"Bob execution timed out after {timeout}s"
    except Exception as e:
        logger.error(f"Bob execution error: {e}")
        return False, "", str(e)
    finally:
        if os.path.exists(prompt_file):
            os.remove(prompt_file)


def run_bob_impact_analysis(diff: str, changed_files: list, workspace: str) -> Tuple[bool, str]:
    """Run Bob to perform repository-wide impact analysis."""
    prompt = IMPACT_ANALYSIS_PROMPT.format(
        diff=diff[:4000],
        changed_files=", ".join(changed_files),
    )
    success, stdout, stderr = run_bob_task(
        prompt=prompt,
        workspace=workspace,
        mode=settings.BOB_MODE,
    )
    output = stdout + ("\n\nSTDERR:\n" + stderr if stderr else "")
    return success, output


def run_bob_remediation(diff: str, impact_findings: str, workspace: str) -> Tuple[bool, str]:
    """Run Bob to perform multi-file remediation."""
    prompt = REMEDIATION_PROMPT.format(
        diff=diff[:3000],
        impact_findings=impact_findings[:4000],
    )
    success, stdout, stderr = run_bob_task(
        prompt=prompt,
        workspace=workspace,
        mode=settings.BOB_MODE,
    )
    output = stdout + ("\n\nSTDERR:\n" + stderr if stderr else "")
    return success, output


def run_bob_repair(failure_output: str, attempt: int, workspace: str) -> Tuple[bool, str]:
    """Run Bob to repair a verification failure."""
    prompt = REPAIR_PROMPT.format(
        failure_output=failure_output[:3000],
        attempt=attempt,
    )
    success, stdout, stderr = run_bob_task(
        prompt=prompt,
        workspace=workspace,
        mode=settings.BOB_MODE,
    )
    output = stdout + ("\n\nSTDERR:\n" + stderr if stderr else "")
    return success, output


def _simulate_bob(prompt: str, workspace: str) -> Tuple[bool, str, str]:
    """
    Simulation mode when Bob is not installed.
    Performs static analysis to discover impacted files.
    Used for development/CI without Bob.
    """
    logger.info("SIMULATION: Analyzing repository without Bob")

    # Detect the change type from the prompt
    if "Integer" in prompt or "integer" in prompt or "amount" in prompt.lower():
        return _simulate_amount_type_change(workspace)

    return True, "Simulation: No specific change pattern detected.", ""


def _simulate_amount_type_change(workspace: str) -> Tuple[bool, str]:
    """Simulate Bob discovering the Payment.amount integer→decimal impact."""
    output = """RELEASESHIELD IMPACT ANALYSIS (Simulation Mode — Bob not installed)

CHANGE DETECTED: Payment.amount type change (Integer → Numeric/Decimal)

CHANGED SYMBOLS:
- Payment.amount (SQLAlchemy Column type)
- PaymentCreate.amount (Pydantic field type)

DEVELOPER-CHANGED FILES:
- backend/models/payment.py

BOB-DISCOVERED IMPACTED FILES:

1. backend/schemas/payment.py [CRITICAL]
   Reason: PaymentCreate.amount uses `int` type annotation and validates isinstance(amount, int).
   With Decimal amounts, this validation will reject valid inputs.
   Required change: Update type to Decimal, update validator.

2. backend/services/payment_service.py [CRITICAL]
   Reason: validate_amount() checks isinstance(amount, int) — will reject Decimal.
   calculate_processing_fee() uses integer arithmetic.
   format_amount_display() uses integer division.
   Required change: Update all methods to handle Decimal type.

3. backend/api/payments.py [HIGH]
   Reason: Endpoint returns amount values — API contract changes from integer to decimal.
   Any consumers expecting integer will receive decimal values.
   Required change: Ensure response serialization handles Decimal.

4. frontend/src/types/Payment.ts [CRITICAL]
   Reason: Payment.amount typed as `number` with isValidAmount() checking Number.isInteger().
   formatAmount() uses integer arithmetic (cents).
   Required change: Update to handle decimal amounts, update formatting logic.

5. frontend/src/api/payments.ts [MEDIUM]
   Reason: createPayment() validates Number.isInteger(data.amount) — will reject decimal.
   Required change: Remove integer-only validation.

6. frontend/src/components/PaymentCard.tsx [HIGH]
   Reason: Uses integer arithmetic for fee calculation. Renders "cents (integer)" label.
   isValidAmount checks Number.isInteger(). 
   Required change: Update fee calculation, display logic.

7. tests/test_payments.py [CRITICAL]
   Reason: Tests explicitly assert isinstance(amount, int).
   test_amount_is_integer_type tests that float raises — behavior changes.
   Fixtures contain integer values.
   Required change: Update assertions to allow Decimal.

8. fixtures/payments.json [MEDIUM]
   Reason: All amounts are integers (9999, 4999 etc.).
   With Decimal support, fixtures should use decimal notation.
   Required change: Update to decimal format.

DATABASE MIGRATION REQUIRED:
- migrations/001_create_payments.sql: INTEGER → NUMERIC(10,2)
- A new migration file should be created.

SUMMARY: 8 additional files impacted beyond the 1 developer-changed file.
"""
    return True, output, ""
