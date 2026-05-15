"""Tests for Friday experience optimization modules."""
import time
import pytest
from claw_mem.enhanced_retriever import EnhancedRetriever
from claw_mem.proactive_trigger import ProactiveTrigger
from claw_mem.natural_decay import NaturalDecay


class TestEnhancedRetriever:
    def setup_method(self):
        self.er = EnhancedRetriever()

    def test_search_basic(self):
        memories = [
            {"id": "1", "content": "Project Neo architecture review"},
            {"id": "2", "content": "bug fix in memory module"},
            {"id": "3", "content": "unrelated weather data"},
        ]
        results = self.er.search("Neo architecture", memories, limit=2)
        assert len(results) > 0
        assert results[0]["id"] == "1"

    def test_score_present(self):
        memories = [{"id": "1", "content": "test query match"}]
        results = self.er.search("test query", memories)
        assert "enhanced_score" in results[0]


class TestProactiveTrigger:
    def setup_method(self):
        self.pt = ProactiveTrigger()

    def test_time_trigger(self):
        self.pt.add_time_trigger("mem_1", time.time() - 10, "reminder")
        fired = self.pt.check_triggers()
        assert len(fired) == 1

    def test_time_trigger_future_not_fired(self):
        self.pt.add_time_trigger("mem_2", time.time() + 9999, "future")
        fired = self.pt.check_triggers()
        assert len(fired) == 0

    def test_event_trigger(self):
        self.pt.add_event_trigger("mem_3", "mention:Project Neo", "discussing Neo")
        fired = self.pt.check_triggers({"topic": "Project Neo architecture"})
        assert len(fired) == 1

    def test_event_no_match(self):
        self.pt.add_event_trigger("mem_4", "mention:quantum", "physics")
        fired = self.pt.check_triggers({"topic": "Python programming"})
        assert len(fired) == 0


class TestNaturalDecay:
    def setup_method(self):
        self.nd = NaturalDecay(decay_rate=0.5)

    def test_recent_memory(self):
        mem = {"salience_score": 0.8, "timestamp": time.time()}
        score = self.nd.calculate_importance(mem)
        assert score > 0.7

    def test_old_memory(self):
        mem = {"salience_score": 0.8, "timestamp": time.time() - 7*86400}
        score = self.nd.calculate_importance(mem)
        assert score < 0.5

    def test_important_protection(self):
        mem = {"salience_score": 0.9, "timestamp": time.time() - 30*86400}
        score = self.nd.calculate_importance(mem)
        assert score >= 0.9 * 0.3  # protected floor
