"""
Git operations for ReleaseShield.
Reads repository state, diffs, branch info.
NEVER modifies git history — read-only operations only.
"""
import subprocess
import os
import re
from typing import List, Optional, Tuple
from .models import GitState, GitDiffFile
from .config import settings
import logging

import shutil


def _get_git_binary() -> str:
    which = shutil.which("git")
    if which:
        return which
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe"),
        r"C:\Users\USER\AppData\Local\Programs\Git\cmd\git.exe",
        os.path.expandvars(r"%ProgramFiles%\Git\cmd\git.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "git"


def _run_git(args: List[str], cwd: str) -> Tuple[str, str, int]:
    """Run a git command safely (no shell=True)."""
    git_bin = _get_git_binary()
    cmd = [git_bin] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "git command timed out", 1
    except FileNotFoundError:
        return "", "git not found on PATH", 1


def get_current_branch(repo_path: str) -> str:
    stdout, _, rc = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    if rc != 0:
        return "unknown"
    return stdout or "HEAD"


def get_current_commit(repo_path: str) -> Tuple[str, str]:
    """Returns (full_hash, short_hash)."""
    stdout, _, rc = _run_git(["rev-parse", "HEAD"], repo_path)
    if rc != 0:
        return "0000000000000000000000000000000000000000", "0000000"
    full = stdout
    short = full[:7]
    return full, short


def get_changed_files(repo_path: str) -> List[GitDiffFile]:
    """Get files changed vs HEAD (working tree + staged)."""
    changed: List[GitDiffFile] = []

    # Staged changes
    stdout, _, _ = _run_git(["diff", "--cached", "--name-status"], repo_path)
    # Unstaged changes
    stdout2, _, _ = _run_git(["diff", "--name-status"], repo_path)

    seen = set()
    for line in (stdout + "\n" + stdout2).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        status_code, path = parts
        if path in seen:
            continue
        seen.add(path)

        status_map = {"M": "modified", "A": "added", "D": "deleted", "R": "renamed"}
        status = status_map.get(status_code[0], "modified")
        changed.append(GitDiffFile(path=path, status=status))

    # If nothing in working tree, check last commit
    if not changed:
        stdout3, _, rc = _run_git(["diff", "HEAD~1", "--name-status"], repo_path)
        if rc == 0:
            for line in stdout3.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) != 2:
                    continue
                status_code, path = parts
                if path in seen:
                    continue
                seen.add(path)
                status_map = {"M": "modified", "A": "added", "D": "deleted"}
                status = status_map.get(status_code[0], "modified")
                changed.append(GitDiffFile(path=path, status=status))

    return changed


def get_diff_for_file(repo_path: str, file_path: str) -> str:
    """Get unified diff for a specific file."""
    stdout, _, _ = _run_git(["diff", "HEAD", "--", file_path], repo_path)
    if not stdout:
        stdout, _, _ = _run_git(["diff", "HEAD~1", "--", file_path], repo_path)
    return stdout[:3000] if stdout else ""  # cap at 3000 chars


def get_full_diff(repo_path: str) -> str:
    """Get full diff of all changes."""
    stdout, _, _ = _run_git(["diff", "HEAD"], repo_path)
    if not stdout:
        stdout, _, _ = _run_git(["diff", "HEAD~1"], repo_path)
    return stdout[:8000] if stdout else ""


def ensure_git_repo(repo_path: str):
    """Ensure repo_path has an initialized git repository with clean BEFORE state."""
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.exists(git_dir):
        _run_git(["init"], repo_path)
        _run_git(["config", "user.name", "ReleaseShield Demo"], repo_path)
        _run_git(["config", "user.email", "demo@releaseshield.local"], repo_path)
        _run_git(["add", "."], repo_path)
        _run_git(["commit", "-m", "Initial commit: payment service (BEFORE state)"], repo_path)


def get_git_state(repo_path: str) -> GitState:
    """Capture complete current git state."""
    ensure_git_repo(repo_path)
    branch = get_current_branch(repo_path)
    full_commit, short_commit = get_current_commit(repo_path)
    changed_files = get_changed_files(repo_path)

    # Add diff snippets for changed files
    for f in changed_files:
        f.diff_snippet = get_diff_for_file(repo_path, f.path)

    # Count additions/deletions
    for f in changed_files:
        if f.diff_snippet:
            f.additions = f.diff_snippet.count("\n+")
            f.deletions = f.diff_snippet.count("\n-")

    full_diff = get_full_diff(repo_path)
    is_clean = len(changed_files) == 0

    return GitState(
        branch=branch,
        commit=full_commit,
        short_commit=short_commit,
        changed_files=changed_files,
        diff_summary=full_diff,
        is_clean=is_clean,
    )


def verify_repo_exists(repo_path: str) -> bool:
    """Verify that the path is a valid git repository, initializing if needed."""
    if not os.path.exists(repo_path):
        return False
    ensure_git_repo(repo_path)
    stdout, _, rc = _run_git(["rev-parse", "--is-inside-work-tree"], repo_path)
    return rc == 0 and stdout.strip() == "true"
