# Copyright 2026 Peter Cheng
"""Tests for cms/state_machine.py."""

import pytest
from claw_mem.cms.state_machine import (
    SessionState,
    StateEvent,
    TRANSITIONS,
    StateTransition,
    SessionStateMachine,
)


class TestSessionState:
    def test_values(self):
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.PAUSED.value == "paused"
        assert SessionState.COMPRESSED.value == "compressed"
        assert SessionState.ARCHIVED.value == "archived"

    def test_all_states_in_transitions(self):
        for state in SessionState:
            assert state in TRANSITIONS


class TestStateEvent:
    def test_values(self):
        assert StateEvent.PAUSE.value == "pause"
        assert StateEvent.RESUME.value == "resume"
        assert StateEvent.COMPRESS.value == "compress"
        assert StateEvent.ARCHIVE.value == "archive"
        assert StateEvent.RESTORE.value == "restore"


class TestTransitions:
    def test_active_transitions(self):
        allowed = TRANSITIONS[SessionState.ACTIVE]
        assert StateEvent.PAUSE in allowed
        assert StateEvent.COMPRESS in allowed
        assert StateEvent.ARCHIVE in allowed
        assert allowed[StateEvent.PAUSE] == SessionState.PAUSED

    def test_paused_transitions(self):
        allowed = TRANSITIONS[SessionState.PAUSED]
        assert StateEvent.RESUME in allowed
        assert allowed[StateEvent.RESUME] == SessionState.ACTIVE

    def test_archived_transitions(self):
        allowed = TRANSITIONS[SessionState.ARCHIVED]
        assert StateEvent.RESTORE in allowed
        assert allowed[StateEvent.RESTORE] == SessionState.ACTIVE


class TestStateTransition:
    def test_create(self):
        t = StateTransition(session_id="s1", from_state="active", to_state="paused", event="pause")
        assert t.session_id == "s1"
        assert t.from_state == "active"
        assert t.to_state == "paused"

    def test_to_dict(self):
        t = StateTransition(
            session_id="s1", from_state="active", to_state="compressed", event="compress"
        )
        d = t.to_dict()
        assert d["session_id"] == "s1"
        assert d["from_state"] == "active"
        assert d["event"] == "compress"


class TestSessionStateMachine:
    @pytest.fixture
    def sm(self):
        return SessionStateMachine()

    def test_initial_state_is_active(self, sm):
        assert sm.get_current_state("s1") == "active"

    def test_transition_active_to_paused(self, sm):
        t = sm.transition("s1", StateEvent.PAUSE)
        assert t.from_state == "active"
        assert t.to_state == "paused"
        assert sm.get_current_state("s1") == "paused"

    def test_transition_active_to_compressed(self, sm):
        t = sm.transition("s1", StateEvent.COMPRESS)
        assert t.to_state == "compressed"
        assert sm.get_current_state("s1") == "compressed"

    def test_transition_active_to_archived(self, sm):
        t = sm.transition("s1", StateEvent.ARCHIVE)
        assert t.to_state == "archived"
        assert sm.get_current_state("s1") == "archived"

    def test_transition_paused_to_active(self, sm):
        sm.transition("s1", StateEvent.PAUSE)
        t = sm.transition("s1", StateEvent.RESUME)
        assert t.to_state == "active"

    def test_transition_archived_to_active(self, sm):
        sm.transition("s1", StateEvent.ARCHIVE)
        t = sm.transition("s1", StateEvent.RESTORE)
        assert t.to_state == "active"

    def test_invalid_transition_raises(self, sm):
        sm.transition("s1", StateEvent.PAUSE)
        with pytest.raises(ValueError, match="Invalid transition"):
            sm.transition("s1", StateEvent.PAUSE)

    def test_history_tracking(self, sm):
        sm.transition("s1", StateEvent.PAUSE)
        sm.transition("s1", StateEvent.RESUME)
        history = sm.get_state_history("s1")
        assert len(history) == 2
        assert history[0].event == "pause"
        assert history[1].event == "resume"

    def test_empty_history(self, sm):
        assert sm.get_state_history("nonexistent") == []

    def test_set_state_valid(self, sm):
        sm.set_state("s1", "compressed")
        assert sm.get_current_state("s1") == "compressed"

    def test_set_state_invalid_defaults_to_active(self, sm):
        sm.transition("s1", StateEvent.PAUSE)
        sm.set_state("s1", "invalid_state")
        assert sm.get_current_state("s1") == "active"

    def test_transition_with_metadata(self, sm):
        t = sm.transition("s1", StateEvent.PAUSE, metadata={"reason": "timeout"})
        assert t.metadata["reason"] == "timeout"

    def test_multiple_sessions(self, sm):
        sm.transition("a", StateEvent.PAUSE)
        sm.transition("b", StateEvent.COMPRESS)
        assert sm.get_current_state("a") == "paused"
        assert sm.get_current_state("b") == "compressed"

    def test_full_lifecycle(self, sm):
        sm.transition("s1", StateEvent.PAUSE)
        sm.transition("s1", StateEvent.RESUME)
        sm.transition("s1", StateEvent.COMPRESS)
        sm.transition("s1", StateEvent.EXPAND)
        sm.transition("s1", StateEvent.ARCHIVE)
        sm.transition("s1", StateEvent.RESTORE)
        assert sm.get_current_state("s1") == "active"
        assert len(sm.get_state_history("s1")) == 6
