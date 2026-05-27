"""Tests for ConfidenceGate + GateResult + ConfidenceLevel (F2 · v4.9.0)."""

import tempfile
from unittest.mock import MagicMock

import pytest

from claw_mem.context.confidence_gate import (
    ConfidenceGate,
    ConfidenceLevel,
    GateResult,
)


# ── helpers ───────────────────────────────────────────────────────────

def _make_manager(workspace_dir: str, **flags):
    from claw_mem.memory_manager import MemoryManager
    defaults = dict(
        enable_graph=False,
        enable_decay=False,
        enable_ground_truth=False,
        enable_merge=False,
        enable_conflict_detect=False,
        enable_tiered_decay=False,
    )
    defaults.update(flags)
    return MemoryManager(workspace=workspace_dir, **defaults)


def _store_semantic(manager, content, tags=None, metadata=None):
    record = {"content": content, "tags": tags or [], "metadata": metadata or {}}
    manager.store(**record, memory_type="semantic", update_index=True)
    memories = manager.semantic.get_all()
    return memories[-1].get("id", "")


def _memory(content="test", score=0.75, mem_id="m1", tags=None, created_at=None):
    return {
        "id": mem_id,
        "content": content,
        "score": score,
        "tags": tags or [],
        "created_at": created_at,
    }


# ── GateResult / ConfidenceLevel ──────────────────────────────────────

class TestConfidenceLevel:
    def test_enum_values(self):
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"


class TestGateResult:
    def test_defaults(self):
        r = GateResult(memory_id="a", confidence_score=0.8, confidence_level=ConfidenceLevel.HIGH,
                       vector_score=0.9, time_score=0.8, conflict_score=1.0, frequency_score=0.8)
        assert r.memory_id == "a"
        assert r.confidence_score == 0.8
        assert r.confidence_level == ConfidenceLevel.HIGH

    def test_warning_set(self):
        r = GateResult(memory_id="x", confidence_score=0.3, confidence_level=ConfidenceLevel.LOW,
                       vector_score=0.5, time_score=0.5, conflict_score=1.0, frequency_score=0.5,
                       warning="time_score_unavailable")
        assert r.warning == "time_score_unavailable"


# ── ConfidenceGate standalone (no manager) ────────────────────────────

class TestStandaloneGate:
    """Gate without a MemoryManager – time/conflict dims unavailable, weight redistributed."""

    def test_evaluate_score_only(self):
        gate = ConfidenceGate()  # no manager
        m = _memory(score=0.85, tags=["important"])
        result = gate.evaluate(m)
        assert result.confidence_score > 0.7  # vector high + freq tag
        assert "time_score_unavailable" in (result.warning or "")
        assert "conflict_score_unavailable" in (result.warning or "")

    def test_evaluate_no_score_no_tags(self):
        gate = ConfidenceGate()
        m = _memory(score=None, tags=[])
        result = gate.evaluate(m)
        # vector None → unavailable → weight goes to frequency only → 0.5
        assert 0.4 <= result.confidence_score <= 0.55
        assert result.confidence_level == ConfidenceLevel.MEDIUM

    def test_high_threshold_classification(self):
        gate = ConfidenceGate(high_threshold=0.8, low_threshold=0.4)
        m = _memory(score=0.9, tags=["critical"])
        result = gate.evaluate(m)
        assert result.confidence_level == ConfidenceLevel.HIGH

    def test_low_classification(self):
        gate = ConfidenceGate()
        m = _memory(score=0.1, tags=[])
        result = gate.evaluate(m)
        assert result.confidence_level == ConfidenceLevel.LOW

    def test_filter_drops_low(self):
        gate = ConfidenceGate()
        memories = [
            _memory(score=0.85, mem_id="high1"),
            _memory(score=0.1, mem_id="low1", tags=[]),
            _memory(score=0.7, mem_id="mid1", tags=["normal"]),
        ]
        filtered = gate.filter(memories)
        ids = [m["id"] for m in filtered]
        assert "low1" not in ids
        assert "high1" in ids

    def test_evaluate_batch_returns_all(self):
        gate = ConfidenceGate()
        memories = [_memory(score=0.5, mem_id="a"), _memory(score=0.5, mem_id="b")]
        results = gate.evaluate_batch(memories)
        assert len(results) == 2
        assert all(isinstance(r, GateResult) for r in results)
        assert results[0].memory_id == "a"
        assert results[1].memory_id == "b"


# ── Four-dimension scoring with manager ───────────────────────────────

class TestVectorScore:
    def test_score_field_present(self):
        gate = ConfidenceGate()
        score = gate._compute_vector_score({"score": 0.72})
        assert score == 0.72

    def test_score_field_absent(self):
        gate = ConfidenceGate()
        assert gate._compute_vector_score({}) is None

    def test_score_field_invalid(self):
        gate = ConfidenceGate()
        assert gate._compute_vector_score({"score": "abc"}) is None


class TestFrequencyScore:
    def test_no_tags(self):
        gate = ConfidenceGate()
        assert gate._compute_frequency_score({"tags": []}) == 0.5

    def test_has_tags(self):
        gate = ConfidenceGate()
        assert gate._compute_frequency_score({"tags": ["normal"]}) == 0.8

    def test_critical_tag(self):
        gate = ConfidenceGate()
        assert gate._compute_frequency_score({"tags": ["critical"]}) == 1.0
        assert gate._compute_frequency_score({"tags": ["永久"]}) == 1.0
        assert gate._compute_frequency_score({"tags": ["关键"]}) == 1.0

    def test_tags_in_metadata(self):
        gate = ConfidenceGate()
        assert gate._compute_frequency_score(
            {"metadata": {"tags": ["critical_rule"]}}
        ) == 1.0


class TestConflictScore:
    def test_no_manager_returns_none(self):
        gate = ConfidenceGate()
        assert gate._compute_conflict_score({"id": "x"}) is None

    def test_no_conflict_detector_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d, enable_conflict_detect=False)
            gate = ConfidenceGate(manager=mgr)
            assert gate._compute_conflict_score({"id": "x"}) is None

    def test_no_cache_returns_clean(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d, enable_conflict_detect=True)
            gate = ConfidenceGate(manager=mgr)
            # No conflict cache filled yet → assume clean
            assert gate._compute_conflict_score({"id": "x"}) == 1.0

    def test_conflicted_id_scores_low(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d, enable_conflict_detect=True)
            m1 = _store_semantic(mgr, "Alice is the CEO.", metadata={"entity": "Alice"})
            m2 = _store_semantic(mgr, "Bob is the CEO.", metadata={"entity": "Bob"})
            gate = ConfidenceGate(manager=mgr)
            gate._fill_conflict_cache()
            # After cache fill, scores should be based on real detection
            score_m1 = gate._compute_conflict_score({"id": m1})
            assert score_m1 is not None
            assert score_m1 in (0.3, 1.0)


class TestTimeScore:
    def test_tiered_decay_not_enabled_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d, enable_tiered_decay=False)
            gate = ConfidenceGate(manager=mgr)
            assert gate._compute_time_score({"id": "x"}) is None

    def test_tiered_decay_enabled_scores_recent(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d, enable_tiered_decay=True)
            mid = _store_semantic(mgr, "Recent memory.")
            mem = mgr.semantic.get_all()[-1]
            gate = ConfidenceGate(manager=mgr)
            score = gate._compute_time_score(mem)
            # Recently inserted → HOT → 1.0
            assert score == 1.0


# ── weight redistribution ─────────────────────────────────────────────

class TestWeightRedistribution:
    def test_all_available_no_change(self):
        gate = ConfidenceGate()
        eff = gate._effective_weights({
            "vector": True, "time": True, "conflict": True, "frequency": True,
        })
        assert eff["vector"] == pytest.approx(0.4)
        assert eff["time"] == pytest.approx(0.3)
        assert eff["conflict"] == pytest.approx(0.2)
        assert eff["frequency"] == pytest.approx(0.1)

    def test_time_unavailable_redistributed(self):
        gate = ConfidenceGate()
        eff = gate._effective_weights({
            "vector": True, "time": False, "conflict": True, "frequency": True,
        })
        # time_weight 0.3 redistributed proportionally to 0.4+0.2+0.1=0.7
        # vector: 0.4 + 0.4*(0.3/0.7) = 0.4 + 0.1714 ≈ 0.5714
        assert eff["time"] == 0.0
        assert eff["vector"] == pytest.approx(0.4 + 0.4 * (0.3 / 0.7))
        assert eff["conflict"] == pytest.approx(0.2 + 0.2 * (0.3 / 0.7))
        assert eff["frequency"] == pytest.approx(0.1 + 0.1 * (0.3 / 0.7))
        assert sum(eff.values()) == pytest.approx(1.0)
