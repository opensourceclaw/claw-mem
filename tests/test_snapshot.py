"""Tests for SnapshotStorage (v3.0.0-rc.3)."""
import tempfile, pytest
from claw_mem.cms.snapshot import SnapshotStorage, SessionSnapshot

class TestSnapshotStorage:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.store = SnapshotStorage(self.tmp)

    def test_save_and_load(self):
        sid = self.store.save("sess_a", state="active", memory_ids=["m1","m2"])
        snap = self.store.load(sid)
        assert snap is not None
        assert snap.session_id == "sess_a"
        assert snap.state == "active"
        assert snap.memory_ids == ["m1","m2"]

    def test_list_snapshots(self):
        self.store.save("s1", memory_ids=["a"])
        self.store.save("s1", memory_ids=["b"])
        snaps = self.store.list("s1")
        assert len(snaps) >= 2

    def test_delete(self):
        sid = self.store.save("s2", memory_ids=["x"])
        assert self.store.delete(sid)
        assert self.store.load(sid) is None

    def test_list_empty_session(self):
        assert self.store.list("nonexistent") == []

    def test_checksum(self):
        snap = SessionSnapshot("s1", "snap_test", state="active", memory_ids=["a","b"])
        cs = snap.compute_checksum()
        assert len(cs) == 16

    def test_to_dict_roundtrip(self):
        snap = SessionSnapshot("s", "id", state="paused", memory_ids=["m1"])
        snap.checksum = snap.compute_checksum()
        d = snap.to_dict()
        snap2 = SessionSnapshot.from_dict(d)
        assert snap2.snapshot_id == "id"
        assert snap2.state == "paused"

    def test_workspace_subdirs(self):
        self.store.save("s/a", memory_ids=["1"])
        snaps = self.store.list("s/a")
        assert len(snaps) == 1
