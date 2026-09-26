#!/usr/bin/env python3
"""
ReleaseShield setup script.
Installs Python dependencies and sets up the project for the demo.
"""
import subprocess
import sys
import os
from pathlib import Path


def run(cmd, cwd=None, check=True):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    if check and result.returncode != 0:
        print(f"  ERROR: command failed with code {result.returncode}")
        sys.exit(result.returncode)
    return result


def main():
    root = Path(__file__).parent
    demo_repo = root / "demo-repo"

    print("=" * 60)
    print("ReleaseShield Setup")
    print("=" * 60)

    # 1. Install backend (ReleaseShield) dependencies
    print("\n[1/4] Installing ReleaseShield backend dependencies...")
    run([sys.executable, "-m", "pip", "install", "-r", str(root / "requirements.txt")])

    # 2. Install demo-repo dependencies
    print("\n[2/4] Installing demo-repo dependencies...")
    run([sys.executable, "-m", "pip", "install", "-r", str(demo_repo / "requirements.txt")])

    # 3. Initialize git repo in demo-repo (if not already)
    print("\n[3/4] Initializing demo-repo git repository...")
    git_dir = demo_repo / ".git"
    if not git_dir.exists():
        run(["git", "init"], cwd=demo_repo)
        run(["git", "add", "."], cwd=demo_repo)
        run(["git", "commit", "-m", "Initial commit: payment service (BEFORE state)"], cwd=demo_repo)
        print("  [OK] Git repository initialized with BEFORE state committed")
    else:
        print("  [OK] Git repository already exists")

    # 4. Copy .env.example to .env if not exists
    print("\n[4/4] Setting up environment...")
    env_file = root / ".env"
    env_example = root / ".env.example"
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy2(env_example, env_file)
        print(f"  [OK] Created .env from .env.example")
    else:
        print(f"  [OK] .env already exists")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print()
    print("VERIFY setup:")
    print(f"  cd demo-repo && pytest tests/ -v")
    print()
    print("START ReleaseShield:")
    print("  Terminal 1: uvicorn backend.main:app --reload --port 8000")
    print("  Terminal 2: cd frontend && npm install && npm run dev")
    print()
    print("RUN DEMO:")
    print("  python demo/introduce_change.py")
    print("  Then open http://localhost:3000")


if __name__ == "__main__":
    main()
