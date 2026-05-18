# Copyright 2026 Peter Cheng
"""Session state machine for CMS Phase 3 (v3.0.0-rc.3)."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SessionState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPRESSED = "compressed"
    ARCHIVED = "archived"


class StateEvent(Enum):
    PAUSE = "pause"
    RESUME = "resume"
    COMPRESS = "compress"
    EXPAND = "expand"
    ARCHIVE = "archive"
    RESTORE = "restore"


# Valid transitions
TRANSITIONS: Dict[SessionState, Dict[StateEvent, SessionState]] = {
    SessionState.ACTIVE: {
        StateEvent.PAUSE: SessionState.PAUSED,
        StateEvent.COMPRESS: SessionState.COMPRESSED,
        StateEvent.ARCHIVE: SessionState.ARCHIVED,
    },
    SessionState.PAUSED: {
        StateEvent.RESUME: SessionState.ACTIVE,
        StateEvent.ARCHIVE: SessionState.ARCHIVED,
    },
    SessionState.COMPRESSED: {
        StateEvent.EXPAND: SessionState.ACTIVE,
        StateEvent.ARCHIVE: SessionState.ARCHIVED,
    },
    SessionState.ARCHIVED: {
        StateEvent.RESTORE: SessionState.ACTIVE,
    },
}


@dataclass
class StateTransition:
    session_id: str
    from_state: str
    to_state: str
    event: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class SessionStateMachine:
    """Manages session state lifecycle.

    States: active → paused | compressed → (back to active) | archived
    """

    def __init__(self):
        self._states: Dict[str, SessionState] = {}
        self._history: Dict[str, List[StateTransition]] = {}

    def transition(
        self, session_id: str, event: StateEvent, metadata: Dict = None
    ) -> StateTransition:
        """Attempt a state transition.

        Args:
            session_id: Session identifier.
            event: StateEvent to apply.
            metadata: Optional transition metadata.

        Returns:
            StateTransition result.

        Raises:
            ValueError if transition is invalid.
        """
        from_state = self._states.get(session_id, SessionState.ACTIVE)
        allowed = TRANSITIONS.get(from_state, {})

        if event not in allowed:
            raise ValueError(f"Invalid transition: {from_state.value} → {event.value}")

        to_state = allowed[event]

        t = StateTransition(
            session_id=session_id,
            from_state=from_state.value,
            to_state=to_state.value,
            event=event.value,
            metadata=dict(metadata) if metadata else {},
        )

        self._states[session_id] = to_state
        self._history.setdefault(session_id, []).append(t)
        return t

    def get_current_state(self, session_id: str) -> str:
        return self._states.get(session_id, SessionState.ACTIVE).value

    def set_state(self, session_id: str, state: str) -> None:
        try:
            self._states[session_id] = SessionState(state)
        except ValueError:
            self._states[session_id] = SessionState.ACTIVE

    def get_state_history(self, session_id: str) -> List[StateTransition]:
        return list(self._history.get(session_id, []))
