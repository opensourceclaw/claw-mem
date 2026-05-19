# Copyright 2026 Peter Cheng
"""Tests for claw_mem.values module."""

import pytest
from pathlib import Path


class TestUserValue:
    """Test UserValue dataclass."""

    def test_create_default(self):
        from claw_mem.values.user_value_store import UserValue
        from datetime import datetime
        uv = UserValue(user_id="test_user")
        assert uv.user_id == "test_user"
        assert uv.principles == []
        assert isinstance(uv.created_at, datetime)

    def test_to_dict(self):
        from claw_mem.values.user_value_store import UserValue
        uv = UserValue(user_id="test_user", principles=["Be honest"])
        d = uv.to_dict()
        assert d["user_id"] == "test_user"
        assert "Be honest" in d["principles"]

    def test_from_dict(self):
        from claw_mem.values.user_value_store import UserValue
        uv = UserValue.from_dict({"user_id": "test_user", "principles": ["Be kind"]})
        assert uv.user_id == "test_user"

    def test_from_dict_partial(self):
        from claw_mem.values.user_value_store import UserValue
        uv = UserValue.from_dict({"user_id": "partial_user"})
        assert uv.user_id == "partial_user"


class TestUserValueStore:
    """Test UserValueStore class."""

    @pytest.fixture
    def store(self, tmp_path):
        from claw_mem.values.user_value_store import UserValueStore
        return UserValueStore(storage_path=tmp_path / "values")

    def test_save_principle(self, store):
        uv = store.save_principle("user1", "Always respect privacy")
        assert "Always respect privacy" in uv.principles

    def test_save_principle_no_duplicate(self, store):
        store.save_principle("user1", "Unique")
        uv = store.save_principle("user1", "Unique")
        assert uv.principles.count("Unique") == 1

    def test_save_preference(self, store):
        uv = store.save_preference("user1", "theme", "dark")
        assert uv.preferences["theme"] == "dark"

    def test_save_red_line(self, store):
        uv = store.save_red_line("user1", "No sharing")
        assert "No sharing" in uv.red_lines

    def test_get_existing(self, store):
        store.save_principle("user1", "P1")
        assert store.get_user_values("user1") is not None

    def test_get_not_found(self, store):
        assert store.get_user_values("nonexistent") is None

    def test_delete_principle(self, store):
        store.save_principle("user1", "P1")
        uv = store.delete_principle("user1", "P1")
        assert "P1" not in uv.principles

    def test_delete_principle_not_found(self, store):
        assert store.delete_principle("nonexistent", "P1") is None

    def test_delete_preference(self, store):
        store.save_preference("user1", "k", "v")
        uv = store.delete_preference("user1", "k")
        assert "k" not in uv.preferences

    def test_delete_red_line(self, store):
        store.save_red_line("user1", "line1")
        uv = store.delete_red_line("user1", "line1")
        assert "line1" not in uv.red_lines

    def test_list_users(self, store):
        store.save_principle("alice", "P1")
        store.save_principle("bob", "P2")
        assert "alice" in store.list_users()

    def test_persistence(self, tmp_path):
        from claw_mem.values.user_value_store import UserValueStore
        p = tmp_path / "v2"
        s1 = UserValueStore(storage_path=p)
        s1.save_principle("user1", "P1")
        s2 = UserValueStore(storage_path=p)
        assert s2.get_user_values("user1") is not None


class TestFeedbackHandler:
    """Test FeedbackHandler class."""

    @pytest.fixture
    def handler(self, tmp_path):
        from claw_mem.values.user_value_store import UserValueStore
        from claw_mem.values.feedback_handler import FeedbackHandler
        return FeedbackHandler(UserValueStore(storage_path=tmp_path / "fb"))

    def test_request_confirmation(self, handler):
        from claw_mem.values.feedback_handler import FeedbackStatus
        s = handler.request_confirmation("user1", "principle", "Be honest")
        assert s.status == FeedbackStatus.PENDING

    def test_accept_principle(self, handler):
        s = handler.request_confirmation("user1", "principle", "Be honest")
        assert handler.process_feedback(s.id, accepted=True)
        uv = handler.value_store.get_user_values("user1")
        assert "Be honest" in uv.principles

    def test_reject(self, handler):
        from claw_mem.values.feedback_handler import FeedbackStatus
        s = handler.request_confirmation("user1", "principle", "Bad")
        handler.process_feedback(s.id, accepted=False)
        assert s.status == FeedbackStatus.REJECTED

    def test_not_found(self, handler):
        assert handler.process_feedback("fake_id", True) is False

    def test_feedback_preference(self, handler):
        s = handler.request_confirmation("user1", "preference", "theme:dark")
        handler.process_feedback(s.id, accepted=True)
        uv = handler.value_store.get_user_values("user1")
        assert uv.preferences.get("theme") == "dark"

    def test_feedback_red_line(self, handler):
        s = handler.request_confirmation("user1", "red_line", "No spam")
        handler.process_feedback(s.id, accepted=True)
        uv = handler.value_store.get_user_values("user1")
        assert "No spam" in uv.red_lines

    def test_get_pending(self, handler):
        handler.request_confirmation("user1", "principle", "P1")
        handler.request_confirmation("user1", "principle", "P2")
        assert len(handler.get_pending_suggestions("user1")) == 2

    def test_get_accepted(self, handler):
        s = handler.request_confirmation("user1", "principle", "P1")
        handler.process_feedback(s.id, accepted=True)
        assert len(handler.get_accepted_suggestions("user1")) == 1

    def test_get_rejected(self, handler):
        s = handler.request_confirmation("user1", "principle", "Bad")
        handler.process_feedback(s.id, accepted=False)
        assert len(handler.get_rejected_suggestions("user1")) == 1

    def test_clear_expired(self, handler):
        from datetime import timedelta
        s = handler.request_confirmation("user1", "principle", "P1")
        s.created_at = s.created_at - timedelta(hours=48)
        assert handler.clear_expired(max_age_hours=24) == 1

    def test_suggest_update(self, handler):
        s = handler.suggest_update({
            "user_id": "user1", "type": "principle", "content": "S"
        })
        assert s.user_id == "user1"

    def test_value_suggestion_to_dict(self):
        from claw_mem.values.feedback_handler import ValueSuggestion
        vs = ValueSuggestion(id="abc", user_id="u1", suggestion_type="p", content="T")
        assert vs.to_dict()["id"] == "abc"


class TestValueBackup:
    """Test ValueBackup class."""

    @pytest.fixture
    def backup(self, tmp_path):
        from claw_mem.values.user_value_store import UserValueStore
        from claw_mem.values.value_backup import ValueBackup
        store = UserValueStore(storage_path=tmp_path / "vb")
        store.save_principle("user1", "P1")
        return ValueBackup(value_store=store, backup_dir=tmp_path / "backups")

    def test_export(self, backup):
        from claw_mem.values.value_backup import BackupMetadata
        meta = backup.export_values("user1")
        assert isinstance(meta, BackupMetadata)
        assert meta.user_id == "user1"

    def test_export_not_found(self, backup):
        with pytest.raises(ValueError):
            backup.export_values("nonexistent")

    def test_import_to_new_user(self, backup):
        meta = backup.export_values("user1")
        assert backup.import_values("user2", Path(meta.file_path))

    def test_import_file_not_found(self, backup):
        with pytest.raises(FileNotFoundError):
            backup.import_values("user1", Path("/nonexistent/file.json"))

    def test_import_overwrite_protection(self, backup):
        meta = backup.export_values("user1")
        with pytest.raises(ValueError):
            backup.import_values("user1", Path(meta.file_path), overwrite=False)

    def test_list_backups(self, backup):
        backup.export_values("user1")
        assert len(backup.list_backups("user1")) >= 1

    def test_list_backups_empty(self, backup):
        assert backup.list_backups("nonexistent") == []

    def test_backup_metadata(self, backup):
        backup.export_values("user1")
        info = backup.backup_metadata("user1")
        assert info["user_id"] == "user1"

    def test_backup_metadata_empty(self, backup):
        info = backup.backup_metadata("nonexistent")
        assert info["backup_count"] == 0

    def test_delete_backup(self, backup):
        meta = backup.export_values("user1")
        assert backup.delete_backup(meta.backup_id) is True

    def test_delete_backup_not_found(self, backup):
        assert backup.delete_backup("fake_id") is False

    def test_backup_metadata_dc(self):
        from claw_mem.values.value_backup import BackupMetadata
        from datetime import datetime, timezone
        bm = BackupMetadata(user_id="u1", backup_id="abc",
            created_at=datetime.now(timezone.utc),
            file_path="/t.json", file_size=100, values_count=3)
        bm2 = BackupMetadata.from_dict(bm.to_dict())
        assert bm2.user_id == "u1"
