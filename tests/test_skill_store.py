"""Tests for SkillStore (F2 · v4.11.0)."""

import pytest

from claw_mem.extraction.skill_extractor import Skill
from claw_mem.extraction.skill_store import SkillStore


# ── helpers ───────────────────────────────────────────────────────────

def _make_skill(name="test", confidence=0.8, source_triplets=2,
                steps=None, applicability="test context",
                source="rule"):
    return Skill(
        name=name,
        steps=steps or ["step 1", "step 2"],
        applicability=applicability,
        confidence=confidence,
        compression_ratio=source_triplets / 1.0,
        source_triplets=source_triplets,
        source=source,
    )


# ── Basic CRUD ────────────────────────────────────────────────────────

class TestSkillStoreCRUD:
    def setup_method(self):
        self.store = SkillStore()

    def test_store_returns_id(self):
        skill = _make_skill()
        sid = self.store.store(skill)
        assert isinstance(sid, str)
        assert len(sid) == 8

    def test_get_existing(self):
        skill = _make_skill(name="管理能力")
        sid = self.store.store(skill)
        result = self.store.get(sid)
        assert result is not None
        assert result.name == "管理能力"

    def test_get_nonexistent(self):
        assert self.store.get("nonexistent") is None

    def test_delete_existing(self):
        skill = _make_skill()
        sid = self.store.store(skill)
        assert self.store.delete(sid) is True
        assert self.store.get(sid) is None

    def test_delete_nonexistent(self):
        assert self.store.delete("nonexistent") is False

    def test_list_all_empty(self):
        assert self.store.list_all() == []

    def test_list_all(self):
        self.store.store(_make_skill(name="A"))
        self.store.store(_make_skill(name="B"))
        skills = self.store.list_all()
        assert len(skills) == 2

    def test_count(self):
        assert self.store.count() == 0
        self.store.store(_make_skill())
        assert self.store.count() == 1
        self.store.store(_make_skill(name="other"))
        assert self.store.count() == 2

    def test_clear(self):
        self.store.store(_make_skill(name="A"))
        self.store.store(_make_skill(name="B"))
        self.store.clear()
        assert self.store.count() == 0
        assert self.store.list_all() == []


# ── Search ────────────────────────────────────────────────────────────

class TestSkillStoreSearch:
    def setup_method(self):
        self.store = SkillStore()

    def test_search_by_name(self):
        self.store.store(_make_skill(name="资源管理"))
        self.store.store(_make_skill(name="软件开发"))
        results = self.store.search("资源")
        assert len(results) == 1
        assert results[0].name == "资源管理"

    def test_search_case_insensitive(self):
        self.store.store(_make_skill(name="Resource Management"))
        results = self.store.search("resource")
        assert len(results) == 1
        results2 = self.store.search("RESOURCE")
        assert len(results2) == 1

    def test_search_by_applicability(self):
        skill = _make_skill(name="test", applicability="当需要管理项目进度时")
        self.store.store(skill)
        results = self.store.search("管理")
        assert len(results) >= 1

    def test_search_no_match(self):
        self.store.store(_make_skill(name="A"))
        results = self.store.search("nonexistent")
        assert results == []

    def test_search_multiple_matches(self):
        self.store.store(_make_skill(name="资源管理", applicability="管理资源"))
        self.store.store(_make_skill(name="项目开发", applicability="开发流程"))
        self.store.store(_make_skill(name="团队管理", applicability="管理团队"))
        results = self.store.search("管理")
        assert len(results) == 2


# ── Merge ─────────────────────────────────────────────────────────────

class TestSkillStoreMerge:
    def setup_method(self):
        self.store = SkillStore()

    def test_same_name_merges(self):
        s1 = _make_skill(name="管理能力", steps=["step A", "step B"],
                         confidence=0.7, source_triplets=2)
        s2 = _make_skill(name="管理能力", steps=["step B", "step C"],
                         confidence=0.9, source_triplets=3)

        sid1 = self.store.store(s1)
        sid2 = self.store.store(s2)

        # Same ID returned
        assert sid1 == sid2
        # Only one skill stored
        assert self.store.count() == 1

    def test_merge_steps_union_no_duplicates(self):
        s1 = _make_skill(name="test", steps=["A", "B", "C"],
                         source_triplets=2)
        s2 = _make_skill(name="test", steps=["B", "C", "D"],
                         source_triplets=3)
        self.store.store(s1)
        sid = self.store.store(s2)

        merged = self.store.get(sid)
        assert merged is not None
        steps = merged.steps
        # Original order preserved (existing first, then new unique)
        assert steps[:3] == ["A", "B", "C"]
        assert "D" in steps
        assert len(steps) == 4

    def test_merge_confidence_weighted_average(self):
        s1 = _make_skill(name="test", confidence=0.6, source_triplets=2)
        s2 = _make_skill(name="test", confidence=0.9, source_triplets=3)
        self.store.store(s1)
        sid = self.store.store(s2)

        merged = self.store.get(sid)
        # (0.6*2 + 0.9*3) / (2+3) = (1.2 + 2.7) / 5 = 0.78
        assert merged.confidence == 0.78

    def test_merge_applicability_takes_longer(self):
        s1 = _make_skill(name="test", applicability="short")
        s2 = _make_skill(name="test", applicability="a longer applicability string")
        self.store.store(s1)
        sid = self.store.store(s2)

        merged = self.store.get(sid)
        assert merged.applicability == "a longer applicability string"

    def test_merge_source_triplets_sum(self):
        s1 = _make_skill(name="test", source_triplets=3)
        s2 = _make_skill(name="test", source_triplets=5)
        self.store.store(s1)
        sid = self.store.store(s2)

        merged = self.store.get(sid)
        assert merged.source_triplets == 8

    def test_merge_source_is_merged(self):
        s1 = _make_skill(name="test", source="rule")
        s2 = _make_skill(name="test", source="llm")
        self.store.store(s1)
        sid = self.store.store(s2)

        merged = self.store.get(sid)
        assert merged.source == "merged"


# ── Edge cases ────────────────────────────────────────────────────────

class TestSkillStoreEdgeCases:
    def setup_method(self):
        self.store = SkillStore()

    def test_store_many_skills(self):
        for i in range(100):
            self.store.store(_make_skill(name=f"skill_{i}"))
        assert self.store.count() == 100

    def test_delete_then_get(self):
        sid = self.store.store(_make_skill(name="test"))
        self.store.delete(sid)
        assert self.store.get(sid) is None
        assert self.store.count() == 0

    def test_clear_then_reuse(self):
        self.store.store(_make_skill(name="test"))
        self.store.clear()
        sid = self.store.store(_make_skill(name="test"))
        assert self.store.count() == 1
        assert self.store.get(sid) is not None

    def test_delete_unlinks_name_index(self):
        sid = self.store.store(_make_skill(name="unique"))
        self.store.delete(sid)
        # Storing same name again should create a new entry (not merge)
        sid2 = self.store.store(_make_skill(name="unique"))
        assert sid2 != sid
        assert self.store.count() == 1
