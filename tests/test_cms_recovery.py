# Copyright 2026 Peter Cheng
"""Tests for cms/recovery.py."""

import pytest
import tempfile
from pathlib import Path
from claw_mem.cms.recovery import RecoveryResult, ValidationResult, RecoveryMechanism
from claw_mem.cms.snapshot import SnapshotStorage


class TestRecoveryResult:
    def test_create(self):
        rr = RecoveryResult(session_id="s1", snapshot_id="snap1", strategy="latest",
                            recovered_count=10)
        assert rr.session_id == "s1"
        assert rr.recovered_count == 10
        assert rr.success is True

    def test_with_errors(self):
        rr = RecoveryResult(session_id="s1", snapshot_id="", strategy="latest",
                            recovered_count=0, errors=["No snapshots available"], success=False)
        assert rr.success is False
        assert "No snapshots available" in rr.errors

    def test_to_dict(self):
        rr = RecoveryResult(session_id="s1", snapshot_id="snap1", strategy="specific",
                            recovered_count=5)
        d = rr.to_dict()
        assert d["session_id"] == "s1"
        assert d["recovered_count"] == 5


class TestValidationResult:
    def test_valid(self):
        vr = ValidationResult(snapshot_id="snap1", is_valid=True)
        assert vr.is_valid is True
        assert vr.issues == []

    def test_invalid(self):
        vr = ValidationResult(snapshot_id="snap1", is_valid=False, issues=["Checksum mismatch"])
        assert vr.is_valid is False
        assert "Checksum mismatch" in vr.issues

    def test_to_dict(self):
        vr = ValidationResult(snapshot_id="snap1", is_valid=False, issues=["Missing"])
        d = vr.to_dict()
        assert d["is_valid"] is False


class TestRecoveryMechanism:
    @pytest.fixture
    def storage(self, tmp_path):
        return SnapshotStorage(str(tmp_path / "snapshots"))

    @pytest.fixture
    def recovery(self, storage):
        return RecoveryMechanism(snapshot_storage=storage)

    def test_recover_no_snapshots(self, recovery):
        result = recovery.recover("s1", strategy="latest")
        assert result.success is False
        assert "No snapshots available" in result.errors

    def test_recover_specific_not_found(self, recovery):
        result = recovery.recover("s1", snapshot_id="fake", strategy="specific")
        assert result.success is False
        assert any('not found' in e for e in result.errors)

    def test_recover_with_snapshot(self, recovery, storage):
        sid = storage.save("s1", state="active", memory_ids=["m1", "m2", "m3"])
        result = recovery.recover("s1", strategy="latest")
        assert result.success is True
        assert result.recovered_count == 3

    def test_recover_specific_snapshot(self, recovery, storage):
        sid = storage.save("s1", state="active", memory_ids=["m1"])
        storage.save("s1", state="paused", memory_ids=["m2", "m3"])
        result = recovery.recover("s1", snapshot_id=sid, strategy="specific")
        assert result.success is True
        assert result.recovered_count == 1

    def test_recover_best_effort(self, recovery, storage):
        storage.save("s1", state="active", memory_ids=["m1", "m2"])
        result = recovery.recover("s1", strategy="best_effort")
        assert result.success is True
        assert result.recovered_count == 2

    def test_list_snapshots(self, recovery, storage):
        storage.save("s1", state="active", memory_ids=["m1"])
        storage.save("s1", state="paused", memory_ids=["m2"])
        snapshots = recovery.list_snapshots("s1")
        assert len(snapshots) == 2

    def test_validate_snapshot_valid(self, recovery, storage):
        sid = storage.save("s1", state="active", memory_ids=["m1"])
        result = recovery.validate_snapshot(sid)
        assert result.is_valid is True

    def test_validate_snapshot_not_found(self, recovery):
        result = recovery.validate_snapshot("nonexistent")
        assert result.is_valid is False
