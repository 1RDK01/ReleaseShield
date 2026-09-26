"""
ReleaseShield configuration — loaded from environment / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


import shutil
import sys

def get_default_bob_executable() -> str:
    if shutil.which("bob"):
        return "bob"
    if shutil.which("bobide"):
        return "bobide"
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\IBM Bob\bin\bobide.cmd"),
        r"C:\Users\USER\AppData\Local\Programs\IBM Bob\bin\bobide.cmd",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "bob"

def get_default_python_executable() -> str:
    if sys.executable:
        return sys.executable
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
        r"C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "python"

def get_default_pytest_executable() -> str:
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\Scripts\pytest.exe"),
        r"C:\Users\USER\AppData\Local\Programs\Python\Python312\Scripts\pytest.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    if shutil.which("pytest"):
        return "pytest"
    return "pytest"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Demo repository path (relative to project root or absolute)
    DEMO_REPO_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo-repo")

    # Bob executable — tries 'bob' on PATH or installed location
    BOB_EXECUTABLE: str = get_default_bob_executable()

    # Bob workspace / mode
    BOB_MODE: str = "release-shield"
    BOB_TIMEOUT: int = 120  # seconds

    # Verification
    MAX_REPAIR_ATTEMPTS: int = 2
    PYTHON_EXECUTABLE: str = get_default_python_executable()
    PYTEST_EXECUTABLE: str = get_default_pytest_executable()

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    # Artifact output directory
    ARTIFACTS_DIR: str = "artifacts"

    # Whether to run actual Bob or simulate (for CI/testing without Bob installed)
    USE_REAL_BOB: bool = True


settings = Settings()

