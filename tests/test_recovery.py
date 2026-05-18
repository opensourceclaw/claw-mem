"""Tests for RecoveryMechanism (v3.0.0-rc.3)."""
import tempfile, pytest
from claw_mem.cms.snapshot import SnapshotStorage
from claw_mem.cms.recovery import RecoveryMechanism, RecoveryResult, ValidationResult

class TestRecoveryMechanism:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.store = SnapshotStorage(self.tmp)
        self.rm = RecoveryMechanism(self.store)

    def test_recover_latest(self):
        self.store.save("s1", state="active", memory_ids=["a","b","c"])
        r = self.rm.recover("s1", strategy="latest")
        assert r.success
        assert r.recovered_count == 3

    def test_recover_specific(self):
        sid = self.store.save("s2", memory_ids=["x","y"])
        r = self.rm.recover("s2", snapshot_id=sid, strategy="specific")
        assert r.success
        assert r.recovered_count == 2

    def test_recover_best_effort(self):
        self.store.save("s1", memory_ids=["m1"])
        r = self.rm.recover("s1", strategy="best_effort")
        assert r.success

    def test_recover_no_snapshots(self):
        r = self.rm.recover("nonexistent", strategy="latest")
        assert not r.success

    def test_validate_valid(self):
        snap = self.store.save("s1", state="active")
        v = self.rm.validate_snapshot(snap)
        assert v.is_valid

    def test_validate_not_found(self):
        v = self.rm.validate_snapshot("nonexistent")
        assert not v.is_valid

    def test_list_snapshots(self):
        self.store.save("s1", memory_ids=["a"])
        self.store.save("s1", memory_ids=["b"])
        snaps = self.rm.list_snapshots("s1")
        assert len(snaps) >= 2

    def test_recovery_result_to_dict(self):
        r = RecoveryResult("s1", "snap_id", "latest", 10)
        d = r.to_dict()
        assert d["session_id"] == "s1"
        assert d["recovered_count"] == 10

    def test_validation_result_to_dict(self):
        v = ValidationResult("snap_a", True)
        d = v.to_dict()
        assert d["is_valid"] is True
