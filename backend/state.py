"""
In-memory workflow state store for ReleaseShield.
Single-instance for demo purposes.
"""
from .models import WorkflowState, AuditEvent
from datetime import datetime
import threading

_state = WorkflowState()
_lock = threading.Lock()


def get_state() -> WorkflowState:
    with _lock:
        return _state


def update_state(**kwargs) -> WorkflowState:
    with _lock:
        for k, v in kwargs.items():
            setattr(_state, k, v)
        return _state


def add_audit_event(message: str, level: str = "info", details: dict = None) -> None:
    with _lock:
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            details=details,
        )
        _state.audit_log.append(event)


def reset_state() -> WorkflowState:
    global _state
    with _lock:
        _state = WorkflowState()
        return _state
