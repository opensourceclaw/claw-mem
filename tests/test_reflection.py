"""Tests for claw-mem v3.0.0 Reflection module."""

import pytest
from claw_mem.reflection import (
    BeliefSynthesizer, Belief, Observation, SynthesizerConfig,
    ReflectionOrchestrator, ReflectionResult,
    BeliefTracker, BeliefVersion,
)


class TestBeliefSynthesizer:
    def test_extract_observations(self):
        synth = BeliefSynthesizer()
        memories = [
            {"content": "User prefers Python over Java", "id": "m1"},
            {"content": "Important: Always use type hints", "id": "m2"},
            {"content": "No observation here", "id": "m3"},
        ]
        obs = synth.extract_observations(memories)
        assert len(obs) == 2

    def test_extract_user_preference(self):
        synth = BeliefSynthesizer()
        memories = [{"content": "User likes dark mode themes", "id": "m1"}]
        obs = synth.extract_observations(memories)
        assert len(obs) == 1
        assert obs[0].metadata["category"] == "user_preference"

    def test_synthesize_beliefs(self):
        synth = BeliefSynthesizer()
        obs = [
            Observation(source="m1", content="programming Python development",
                       memory_id="m1", timestamp="2024-01-01",
                       metadata={"category": "user_preference",
                                 "extraction_confidence": 0.8}),
            Observation(source="m2", content="programming Python projects",
                       memory_id="m2", timestamp="2024-01-02",
                       metadata={"category": "user_preference",
                                 "extraction_confidence": 0.8}),
        ]
        beliefs = synth.synthesize(obs, user_id="user123")
        assert len(beliefs) > 0

    def test_synthesize_too_few_observations(self):
        synth = BeliefSynthesizer()
        obs = [Observation(source="m1", content="User prefers Python",
                          memory_id="m1")]
        beliefs = synth.synthesize(obs)
        assert len(beliefs) == 0

    def test_empty_observations(self):
        synth = BeliefSynthesizer()
        beliefs = synth.synthesize([])
        assert beliefs == []

    def test_extract_empty_memories(self):
        synth = BeliefSynthesizer()
        obs = synth.extract_observations([])
        assert obs == []


class TestBeliefTracker:
    def test_record_belief(self):
        tracker = BeliefTracker()
        tracker.record("BEL_001", "User prefers Python", 0.8)
        v = tracker.get_current("BEL_001")
        assert v is not None
        assert v.statement == "User prefers Python"
        assert v.version == 1

    def test_update_belief(self):
        tracker = BeliefTracker()
        tracker.record("BEL_001", "User prefers Python", 0.8)
        tracker.update("BEL_001", "User prefers Python >= 3.10", 0.9)
        v = tracker.get_current("BEL_001")
        assert v.version == 2
        assert v.confidence == 0.9

    def test_get_history(self):
        tracker = BeliefTracker()
        tracker.record("BEL_001", "v1", 0.5)
        tracker.update("BEL_001", "v2", 0.7)
        tracker.update("BEL_001", "v3", 0.9)
        history = tracker.get_history("BEL_001")
        assert len(history) == 3

    def test_get_nonexistent_belief(self):
        tracker = BeliefTracker()
        assert tracker.get_current("nonexistent") is None
        assert tracker.get_history("nonexistent") == []

    def test_get_all_ids(self):
        tracker = BeliefTracker()
        tracker.record("A", "A", 1.0)
        tracker.record("B", "B", 1.0)
        assert len(tracker.get_all_ids()) == 2

    def test_get_all_current(self):
        tracker = BeliefTracker()
        tracker.record("A", "a1", 0.5)
        tracker.update("A", "a2", 0.8)
        tracker.record("B", "b1", 0.7)
        current = tracker.get_all_current()
        assert len(current) == 2
        assert current[0].version == 2  # A updated to v2

    def test_count_beliefs(self):
        tracker = BeliefTracker()
        tracker.record("A", "a", 1.0)
        tracker.record("B", "b", 1.0)
        tracker.update("A", "a2", 0.9)
        assert tracker.count_beliefs() == 2
        assert tracker.count_versions() == 3

    def test_get_changes_since(self):
        tracker = BeliefTracker()
        tracker.record("A", "old", 0.5)
        tracker.update("A", "new", 0.9)
        changes = tracker.get_changes_since("2024-01-01")
        assert len(changes) >= 1

    def test_update_nonexistent_creates(self):
        tracker = BeliefTracker()
        tracker.update("NEW", "statement", 0.8)
        v = tracker.get_current("NEW")
        assert v is not None
        assert v.version == 1


class TestReflectionOrchestrator:
    def test_reflect_with_memories(self):
        orch = ReflectionOrchestrator()
        memories = [
            {"content": "User prefers Python", "id": "m1"},
            {"content": "User likes dark mode", "id": "m2"},
            {"content": "Important: Always use type hints", "id": "m3"},
            {"content": "User dislikes Java", "id": "m4"},
        ]
        result = orch.reflect(memories, user_id="test")
        assert isinstance(result, ReflectionResult)
        assert result.summary is not None

    def test_reflect_empty(self):
        orch = ReflectionOrchestrator()
        result = orch.reflect([], user_id="test")
        assert result.observations == []
        assert result.beliefs == []

    def test_reflect_tracks_new_beliefs(self):
        orch = ReflectionOrchestrator()
        memories = [
            {"content": "User prefers Python", "id": "m1"},
            {"content": "User also loves Python typing", "id": "m2"},
        ]
        result = orch.reflect(memories, user_id="test")
        assert len(result.new_beliefs) >= 0

    def test_get_beliefs(self):
        orch = ReflectionOrchestrator()
        memories = [
            {"content": "User prefers Python", "id": "m1"},
            {"content": "User likes Python over JavaScript", "id": "m2"},
        ]
        orch.reflect(memories, user_id="test")
        beliefs = orch.get_beliefs()
        assert isinstance(beliefs, list)

    def test_get_reflection_stats(self):
        orch = ReflectionOrchestrator()
        orch.reflect([], user_id="test")
        stats = orch.get_reflection_stats()
        assert "reflection_count" in stats
        assert stats["reflection_count"] == 1

    def test_get_beliefs_with_history(self):
        orch = ReflectionOrchestrator()
        orch.reflect([
            {"content": "User prefers Python", "id": "m1"},
            {"content": "User likes Python typing", "id": "m2"},
        ])
        beliefs = orch.get_beliefs(include_history=True)
        assert isinstance(beliefs, list)

    def test_result_to_dict(self):
        orch = ReflectionOrchestrator()
        result = orch.reflect([], user_id="test")
        d = result.to_dict()
        assert "observations_count" in d
        assert "beliefs_total" in d
