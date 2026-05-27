"""Tests for TieredDecayEngine (F2 · v4.7.0)."""

import tempfile
from datetime import datetime, timedelta

import pytest

from claw_mem.decay.tiered_decay import TierLevel, TieredDecayEngine
from claw_mem.memory_manager import MemoryManager


# ── mock helpers ──────────────────────────────────────────────────────

class _MockLLMProvider:
    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        if "importance" in prompt.lower():
            return "0.5"
        return ""


def _make_manager(workspace_dir: str) -> MemoryManager:
    return MemoryManager(
        workspace=workspace_dir,
        enable_graph=False,
        enable_decay=False,
        enable_ground_truth=False,
    )


def _store_semantic(manager: MemoryManager, content: str,
                    metadata=None, tags=None) -> str:
    manager.store(
        content=content,
        memory_type="semantic",
        tags=tags or [],
        metadata=metadata or {},
        update_index=True,
    )
    memories = manager.semantic.get_all()
    return memories[-1].get("id", "")


# ── tests ─────────────────────────────────────────────────────────────

class TestClassify:
    """Tier classification tests."""

    def test_recent_memory_is_hot(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Recently stored memory.")
            engine = TieredDecayEngine(mgr, hot_ttl=999999)  # very long hot window

            all_m = mgr.semantic.get_all()
            tier = engine.classify(all_m[0])
            assert tier == TierLevel.HOT

    def test_old_memory_is_cold(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Old memory.")
            engine = TieredDecayEngine(mgr, hot_ttl=0, warm_ttl_days=0)  # zero windows

            all_m = mgr.semantic.get_all()
            tier = engine.classify(all_m[0])
            assert tier == TierLevel.COLD

    def test_warm_memory(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Warm memory.")
            engine = TieredDecayEngine(mgr, hot_ttl=0, warm_ttl_days=365)  # tiny hot, huge warm

            all_m = mgr.semantic.get_all()
            tier = engine.classify(all_m[0])
            assert tier == TierLevel.WARM

    def test_deprecated_memory_is_cold(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Deprecated memory.", metadata={"deprecated": "true"})
            engine = TieredDecayEngine(mgr, hot_ttl=999999)

            all_m = mgr.semantic.get_all()
            tier = engine.classify(all_m[0])
            assert tier == TierLevel.COLD


class TestPromote:
    """Memory promotion tests."""

    def test_promote_records_access(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            mid = _store_semantic(mgr, "Test memory.")
            engine = TieredDecayEngine(mgr)

            result = engine.promote(mid)
            assert result is not None

            # Access log should have an entry
            assert mid in engine._access_log
            assert len(engine._access_log[mid]) >= 1

    def test_promote_nonexistent_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            engine = TieredDecayEngine(mgr)
            result = engine.promote("nonexistent-id")
            assert result is None

    def test_promote_empty_id(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            engine = TieredDecayEngine(mgr)
            result = engine.promote("")
            assert result is None


class TestGetImportance:
    """Importance scoring tests."""

    def test_rule_based_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "A short note.")
            engine = TieredDecayEngine(mgr)  # no LLM provider

            all_m = mgr.semantic.get_all()
            score = engine.get_importance(all_m[0])
            assert 0.0 <= score <= 1.0

    def test_long_content_higher_score(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Hi.")
            long_content = "x" * 300
            _store_semantic(mgr, long_content)
            engine = TieredDecayEngine(mgr)

            all_m = mgr.semantic.get_all()
            score_short = engine.get_importance(all_m[0])
            score_long = engine.get_importance(all_m[1])
            assert score_long > score_short

    def test_critical_tag_higher_score(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Random stuff.")
            _store_semantic(mgr, "Important note.", tags=["critical"])
            engine = TieredDecayEngine(mgr)

            all_m = mgr.semantic.get_all()
            score_normal = engine.get_importance(all_m[0])
            score_critical = engine.get_importance(all_m[1])
            assert score_critical > score_normal

    def test_importance_cached(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Cached value test.")
            engine = TieredDecayEngine(mgr)

            all_m = mgr.semantic.get_all()
            score1 = engine.get_importance(all_m[0])
            score2 = engine.get_importance(all_m[0])
            assert score1 == score2  # cached


class TestEvict:
    """Eviction tests."""

    def test_deprecated_evicted_first(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Keep me.")
            _store_semantic(mgr, "Trash.", metadata={"deprecated": "true"})
            engine = TieredDecayEngine(mgr, max_hot=1000, max_warm=1000, max_cold=1000)

            count = engine.evict()
            assert count >= 1

            # Deprecated memory should now have deprecated flag
            all_m = mgr.semantic.get_all()
            deprecated = [m for m in all_m
                          if m.get("metadata", {}).get("deprecated") in ("true", "True")]
            assert len(deprecated) >= 1

    def test_nothing_to_evict(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Only memory.")
            engine = TieredDecayEngine(mgr, max_hot=1000, max_warm=1000, max_cold=1000)

            count = engine.evict()
            assert count == 0


class TestRunCycle:
    """Full cycle tests."""

    def test_cycle_returns_stats(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Memory for stats.")
            engine = TieredDecayEngine(mgr)

            stats = engine.run_cycle()
            assert "total" in stats
            assert "hot" in stats
            assert "warm" in stats
            assert "cold" in stats
            assert "evicted" in stats
            assert "duration_ms" in stats
            assert stats["total"] == 1

    def test_engine_repr(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            engine = TieredDecayEngine(mgr, hot_ttl=60, warm_ttl_days=3, cold_ttl_days=14)
            r = repr(engine)
            assert "60s" in r
            assert "3d" in r
            assert "14d" in r
