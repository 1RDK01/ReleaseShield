"""
Verification engine — runs tests, typecheck, and builds.
Captures output for audit and display.
"""
import subprocess
import time
import os
import re
import logging
from typing import List
from .models import VerificationCommand, VerificationResult
from .config import settings

logger = logging.getLogger("releaseshield.verification")


import shutil

NODE_BIN_DIR = r"C:\Users\USER\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64"

def _get_node_env() -> dict:
    env = os.environ.copy()
    if os.path.exists(NODE_BIN_DIR):
        env["PATH"] = NODE_BIN_DIR + os.pathsep + env.get("PATH", "")
    return env

def _get_node_executable() -> str:
    candidate = os.path.join(NODE_BIN_DIR, "node.exe")
    if os.path.exists(candidate):
        return candidate
    return shutil.which("node") or "node"

def _run_command(
    cmd: List[str],
    cwd: str,
    label: str,
    timeout: int = 120,
) -> VerificationCommand:
    """Run a verification command safely."""
    logger.info(f"Running: {' '.join(cmd)}")
    start = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_get_node_env(),
        )
        duration = time.time() - start
        passed = result.returncode == 0
        stdout = result.stdout
        stderr = result.stderr

    except subprocess.TimeoutExpired:
        duration = timeout
        passed = False
        stdout = ""
        stderr = f"Command timed out after {timeout}s"
        result = None
    except FileNotFoundError as e:
        duration = time.time() - start
        passed = False
        stdout = ""
        stderr = f"Command not found: {e}"
        result = None
    except Exception as e:
        duration = time.time() - start
        passed = False
        stdout = ""
        stderr = str(e)
        result = None

    # Parse test counts from output
    test_count = None
    pass_count = None
    combined_output = stdout + " " + stderr
    match = re.search(r"(\d+)\s+passed", combined_output, re.IGNORECASE)
    if match:
        pass_count = int(match.group(1))
        test_count = pass_count

    fail_match = re.search(r"(\d+)\s+failed", combined_output, re.IGNORECASE)
    if fail_match and pass_count is not None:
        test_count = pass_count + int(fail_match.group(1))

    logger.info(f"  → {label}: {'PASS' if passed else 'FAIL'} ({duration:.1f}s)")

    return VerificationCommand(
        command=" ".join(cmd),
        return_code=result.returncode if result is not None else 1,
        stdout=stdout[:4000],
        stderr=stderr[:2000],
        duration_seconds=round(duration, 2),
        passed=passed,
        label=label,
        test_count=test_count,
        pass_count=pass_count,
    )


def run_backend_tests(repo_path: str) -> VerificationCommand:
    """Run pytest on backend tests."""
    return _run_command(
        cmd=[settings.PYTHON_EXECUTABLE, "-m", "pytest", "tests/", "-q", "--tb=short"],
        cwd=repo_path,
        label="Backend Tests",
        timeout=60,
    )


def run_frontend_typecheck(repo_path: str) -> VerificationCommand:
    """Run TypeScript typecheck."""
    frontend_path = os.path.join(repo_path, "frontend")
    if not os.path.exists(frontend_path):
        return VerificationCommand(
            command="tsc --noEmit",
            return_code=0,
            stdout="Frontend directory not found — skipped",
            stderr="",
            duration_seconds=0,
            passed=True,
            label="TypeScript Check",
        )

    # Locate tsc binary
    local_tsc = os.path.abspath(os.path.join(frontend_path, "node_modules", "typescript", "bin", "tsc"))
    root_tsc = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "node_modules", "typescript", "bin", "tsc"))
    tsc_path = local_tsc if os.path.exists(local_tsc) else (root_tsc if os.path.exists(root_tsc) else None)
    node_exe = _get_node_executable()

    if tsc_path and os.path.exists(node_exe):
        return _run_command(
            cmd=[node_exe, tsc_path, "--noEmit"],
            cwd=frontend_path,
            label="TypeScript Check",
            timeout=60,
        )

    return _run_command(
        cmd=["npx", "tsc", "--noEmit"],
        cwd=frontend_path,
        label="TypeScript Check",
        timeout=60,
    )


def run_frontend_tests(repo_path: str) -> VerificationCommand:
    """Run frontend tests."""
    frontend_path = os.path.join(repo_path, "frontend")
    if not os.path.exists(frontend_path):
        return VerificationCommand(
            command="node test_runner.mjs",
            return_code=0,
            stdout="Frontend directory not found — skipped",
            stderr="",
            duration_seconds=0,
            passed=True,
            label="Frontend Tests",
        )

    test_runner = os.path.abspath(os.path.join(frontend_path, "test_runner.mjs"))
    node_exe = _get_node_executable()

    if os.path.exists(test_runner) and os.path.exists(node_exe):
        return _run_command(
            cmd=[node_exe, test_runner],
            cwd=frontend_path,
            label="Frontend Tests",
            timeout=60,
        )

    return _run_command(
        cmd=["npm", "test", "--", "--watchAll=false", "--passWithNoTests"],
        cwd=frontend_path,
        label="Frontend Tests",
        timeout=90,
    )


def run_full_verification(repo_path: str, attempt: int = 1) -> VerificationResult:
    """Run all verification checks."""
    logger.info(f"Running full verification (attempt {attempt})")
    commands = []

    commands.append(run_backend_tests(repo_path))
    commands.append(run_frontend_typecheck(repo_path))
    commands.append(run_frontend_tests(repo_path))

    all_passed = all(c.passed for c in commands)
    logger.info(f"Verification {'PASSED' if all_passed else 'FAILED'}")

    return VerificationResult(
        all_passed=all_passed,
        commands=commands,
        attempt=attempt,
    )


def get_failure_summary(result: VerificationResult) -> str:
    """Extract failure output for Bob repair prompt."""
    lines = []
    for cmd in result.commands:
        if not cmd.passed:
            lines.append(f"FAILED: {cmd.label}")
            lines.append(f"Command: {cmd.command}")
            if cmd.stderr:
                lines.append(f"STDERR:\n{cmd.stderr[:1000]}")
            if cmd.stdout:
                lines.append(f"STDOUT:\n{cmd.stdout[:1000]}")
            lines.append("")
    return "\n".join(lines)
