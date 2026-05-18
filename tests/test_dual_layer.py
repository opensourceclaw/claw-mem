"""Tests for DualLayerMemory - Two-layer memory organization."""

import pytest
from claw_mem.graph.dual_layer import (
    DualLayerMemory,
    Event,
    Topic,
)


class TestEvent:
    """Unit tests for Event dataclass."""

    def test_create(self):
        evt = Event(
            "evt_1", "Debug session", node_ids=["n1", "n2"], session_id="s1", tags=["debug"]
        )
        assert evt.event_id == "evt_1"
        assert evt.title == "Debug session"
        assert evt.node_ids == ["n1", "n2"]
        assert evt.tags == ["debug"]

    def test_defaults(self):
        evt = Event("evt_x", "Title")
        assert evt.description == ""
        assert evt.node_ids == []
        assert evt.tags == []
        assert evt.session_id is None

    def test_serialize_roundtrip(self):
        evt = Event("e1", "Test", "desc", ["n1"], "s1", 100.0, 200.0, ["t1"])
        d = evt.to_dict()
        evt2 = Event.from_dict(d)
        assert evt2.event_id == "e1"
        assert evt2.node_ids == ["n1"]


class TestTopic:
    """Unit tests for Topic dataclass."""

    def test_create(self):
        tpc = Topic("t1", "AI", keywords=["ai", "ml"])
        assert tpc.topic_id == "t1"
        assert tpc.name == "AI"
        assert tpc.keywords == ["ai", "ml"]

    def test_serialize_roundtrip(self):
        tpc = Topic("t1", "Graph", "desc", ["n1"], ["e1"], ["graph"], 100, 200)
        d = tpc.to_dict()
        tpc2 = Topic.from_dict(d)
        assert tpc2.name == "Graph"
        assert tpc2.keywords == ["graph"]


class TestDualLayerMemory:
    """Unit tests for DualLayerMemory class."""

    def setup_method(self):
        self.dl = DualLayerMemory()

    def test_add_event(self):
        eid = self.dl.add_event("Debug session", node_ids=["n1", "n2"], session_id="sess_a")
        evt = self.dl.get_event(eid)
        assert evt is not None
        assert evt.title == "Debug session"
        assert self.dl.event_count() == 1

    def test_add_event_auto_chain(self):
        """Events in same session should auto-link."""
        e1 = self.dl.add_event("Event 1", session_id="sess_x")
        e2 = self.dl.add_event("Event 2", session_id="sess_x")
        chain = self.dl.get_event_chain(e2)
        assert len(chain) >= 1

    def test_get_event_chain_linear(self):
        e1 = self.dl.add_event("First", session_id="s1")
        e2 = self.dl.add_event("Second", session_id="s1")
        e3 = self.dl.add_event("Third", session_id="s1")
        chain = self.dl.get_event_chain(e3)
        titles = [e.title for e in chain]
        assert "Third" in titles

    def test_get_event_chain_single(self):
        e1 = self.dl.add_event("Only", session_id="s1")
        chain = self.dl.get_event_chain(e1)
        assert len(chain) == 1

    def test_get_event_chain_nonexistent(self):
        chain = self.dl.get_event_chain("nonexistent")
        assert chain == []

    def test_link_events_explicit(self):
        e1 = self.dl.add_event("A")
        e2 = self.dl.add_event("B")
        self.dl.link_events(e1, e2)
        chain = self.dl.get_event_chain(e1)
        assert len(chain) >= 2

    def test_find_events_by_tags(self):
        self.dl.add_event("Bug fix", tags=["bug", "fix"])
        self.dl.add_event("Feature", tags=["feature"])
        found = self.dl.find_events_by_tags(["bug"])
        assert len(found) == 1
        assert found[0].title == "Bug fix"

    def test_find_events_by_session(self):
        self.dl.add_event("E1", session_id="s1")
        self.dl.add_event("E2", session_id="s2")
        self.dl.add_event("E3", session_id="s1")
        found = self.dl.find_events_by_session("s1")
        assert len(found) == 2

    def test_add_topic(self):
        tid = self.dl.add_topic("Graph Performance", keywords=["graph", "performance"])
        tpc = self.dl.get_topic(tid)
        assert tpc is not None
        assert tpc.name == "Graph Performance"
        assert self.dl.topic_count() == 1

    def test_link_topics(self):
        t1 = self.dl.add_topic("A")
        t2 = self.dl.add_topic("B")
        self.dl.link_topics(t1, t2, 0.7)
        related = self.dl.get_related_topics(t1)
        assert len(related) == 1
        assert related[0][1] == 0.7

    def test_get_related_topics_threshold(self):
        t1 = self.dl.add_topic("X")
        t2 = self.dl.add_topic("Y")
        self.dl.link_topics(t1, t2, 0.2)
        related = self.dl.get_related_topics(t1, min_weight=0.3)
        assert len(related) == 0

    def test_search_by_keywords(self):
        self.dl.add_topic("AI", keywords=["ai", "ml", "deep-learning"])
        self.dl.add_topic("Web", keywords=["html", "css"])
        results = self.dl.search_by_keywords(["ai", "web"])
        assert len(results) >= 1

    def test_serialize_roundtrip(self):
        e1 = self.dl.add_event("Event A", session_id="s1", node_ids=["n1"], tags=["important"])
        t1 = self.dl.add_topic("Topic X", keywords=["x"], event_ids=[e1])
        self.dl.link_events(e1, e1)

        d = self.dl.to_dict()
        dl2 = DualLayerMemory.from_dict(d)
        assert dl2.event_count() == self.dl.event_count()
        assert dl2.topic_count() == self.dl.topic_count()

    def test_empty_dual_layer(self):
        assert self.dl.event_count() == 0
        assert self.dl.topic_count() == 0
        d = self.dl.to_dict()
        dl2 = DualLayerMemory.from_dict(d)
        assert dl2.event_count() == 0

    def test_bulk_events(self):
        for i in range(50):
            self.dl.add_event(f"Event {i}", session_id="s1", tags=[f"tag{i % 5}"])
        assert self.dl.event_count() == 50
        found = self.dl.find_events_by_session("s1")
        assert len(found) == 50
