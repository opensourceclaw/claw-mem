"""Tests for SessionStateMachine (v3.0.0-rc.3)."""

import pytest
from claw_mem.cms.state_machine import (
    SessionStateMachine,
    SessionState,
    StateEvent,
    StateTransition,
    TRANSITIONS,
)


class TestSessionStateMachine:
    def setup_method(self):
        self.sm = SessionStateMachine()

    def test_initial_state(self):
        assert self.sm.get_current_state("s1") == "active"

    def test_pause_resume(self):
        self.sm.transition("s1", StateEvent.PAUSE)
        assert self.sm.get_current_state("s1") == "paused"
        self.sm.transition("s1", StateEvent.RESUME)
        assert self.sm.get_current_state("s1") == "active"

    def test_compress_expand(self):
        self.sm.transition("s1", StateEvent.COMPRESS)
        assert self.sm.get_current_state("s1") == "compressed"
        self.sm.transition("s1", StateEvent.EXPAND)
        assert self.sm.get_current_state("s1") == "active"

    def test_archive_restore(self):
        self.sm.transition("s1", StateEvent.PAUSE)
        self.sm.transition("s1", StateEvent.ARCHIVE)
        assert self.sm.get_current_state("s1") == "archived"
        self.sm.transition("s1", StateEvent.RESTORE)
        assert self.sm.get_current_state("s1") == "active"

    def test_invalid_transition(self):
        with pytest.raises(ValueError):
            self.sm.transition("s1", StateEvent.RESUME)  # can't resume from active

    def test_get_history(self):
        self.sm.transition("s1", StateEvent.PAUSE)
        self.sm.transition("s1", StateEvent.RESUME)
        h = self.sm.get_state_history("s1")
        assert len(h) == 2

    def test_transition_metadata(self):
        t = self.sm.transition("s1", StateEvent.COMPRESS, {"reason": "cleanup"})
        assert t.from_state == "active"
        assert t.to_state == "compressed"
        assert t.metadata == {"reason": "cleanup"}

    def test_set_state_direct(self):
        self.sm.set_state("s1", "paused")
        assert self.sm.get_current_state("s1") == "paused"

    def test_set_state_invalid_defaults(self):
        self.sm.set_state("s1", "unknown")
        assert self.sm.get_current_state("s1") == "active"

    def test_multiple_sessions_independent(self):
        self.sm.transition("a", StateEvent.PAUSE)
        assert self.sm.get_current_state("a") == "paused"
        assert self.sm.get_current_state("b") == "active"

    def test_transition_to_dict(self):
        t = self.sm.transition("s1", StateEvent.ARCHIVE)
        d = t.to_dict()
        assert d["session_id"] == "s1"
        assert d["to_state"] == "archived"

    def test_empty_history(self):
        assert self.sm.get_state_history("nonexistent") == []


class TestTransitions:
    def test_all_states_covered(self):
        for state in SessionState:
            assert state in TRANSITIONS

    def test_cant_resume_from_active(self):
        assert StateEvent.RESUME not in TRANSITIONS[SessionState.ACTIVE]
