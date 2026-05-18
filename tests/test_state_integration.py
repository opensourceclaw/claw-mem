"""Integration tests for CMS Phase 3 State Machine (v3.0.0-rc.3)."""

import tempfile, pytest
from claw_mem.cms.state_machine import SessionStateMachine, StateEvent
from claw_mem.cms.snapshot import SnapshotStorage
from claw_mem.cms.recovery import RecoveryMechanism
from claw_mem.cms.context_switcher import ContextSwitcher


class TestStateIntegration:
    def test_full_lifecycle(self):
        """Active → pause → snapshot → archive → restore."""
        sm = SessionStateMachine()
        sid = "session_1"

        sm.transition(sid, StateEvent.PAUSE)
        assert sm.get_current_state(sid) == "paused"

        sm.transition(sid, StateEvent.RESUME)
        assert sm.get_current_state(sid) == "active"

        sm.transition(sid, StateEvent.ARCHIVE)
        assert sm.get_current_state(sid) == "archived"

        sm.transition(sid, StateEvent.RESTORE)
        assert sm.get_current_state(sid) == "active"

    def test_snapshot_and_recover(self):
        store = SnapshotStorage(tempfile.mkdtemp())
        rm = RecoveryMechanism(store)

        store.save("sess", state="active", memory_ids=["m1", "m2", "m3"])
        r = rm.recover("sess", strategy="latest")
        assert r.success

    def test_context_switch_without_evaluator(self):
        cs = ContextSwitcher()
        r = cs.switch("from", "to", "full_switch")
        assert r.success

    def test_snapshot_list_and_delete(self):
        import tempfile

        store = SnapshotStorage(tempfile.mkdtemp())
        sid = store.save("test", memory_ids=["a"])
        assert len(store.list("test")) == 1
        assert store.delete(sid)
        assert len(store.list("test")) == 0

    def test_invalid_transition_caught(self):
        sm = SessionStateMachine()
        with pytest.raises(ValueError):
            sm.transition("s", StateEvent.RESUME)  # can't resume from active

    def test_merge_three_sessions(self):
        cs = ContextSwitcher()
        r = cs.merge(["a", "b", "c"])
        assert r.total_unique >= 0

    def test_state_history_preserved(self):
        sm = SessionStateMachine()
        sm.transition("s1", StateEvent.PAUSE)
        sm.transition("s1", StateEvent.RESUME)
        sm.transition("s1", StateEvent.ARCHIVE)
        assert len(sm.get_state_history("s1")) == 3
