"""GAM: Graph-Augmented Memory — dual-layer architecture."""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EventProgressionGraph:
    """Current session dialogue flow graph."""

    def __init__(self):
        self._events: Dict[str, List[Dict]] = defaultdict(list)

    def add_event(self, session_id: str, text: str) -> None:
        self._events[session_id].append(
            {
                "text": text,
                "timestamp": time.time(),
            }
        )

    def get_session(self, session_id: str, limit: int = 20) -> List[Dict]:
        return self._events.get(session_id, [])[-limit:]

    def count_sessions(self) -> int:
        return len(self._events)


class TopicAssociativeNetwork:
    """Long-term topic associative network."""

    def __init__(self):
        self._topics: Dict[str, List[str]] = defaultdict(list)

    def add_topic(self, topic: str, text: str) -> None:
        self._topics[topic.lower()].append(text)

    def get_by_topic(self, topic: str, limit: int = 5) -> List[str]:
        items = self._topics.get(topic.lower(), [])
        return [t[:200] for t in items[-limit:]]

    def get_related_topics(self, topic: str, limit: int = 5) -> List[str]:
        key = topic.lower()
        related = []
        for t, items in self._topics.items():
            if t != key and key in " ".join(items[-3:]).lower():
                related.append(t)
        return related[:limit]


class DualLayerMemory:
    """GAM: Graph-Augmented Memory — double-layer architecture.

    Layer 1: Event Progression Graph (session flow)
    Layer 2: Topic Associative Network (long-term topics)
    """

    def __init__(self):
        self.event_graph = EventProgressionGraph()
        self.topic_net = TopicAssociativeNetwork()

    def add_interaction(self, text: str, session_id: str) -> None:
        """Record an interaction in both layers."""
        self.event_graph.add_event(session_id, text)

        # Simple topic extraction: keywords as topics
        topics = self._extract_topics(text)
        for topic in topics:
            self.topic_net.add_topic(topic, text)

    def build_context(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Build context from current session."""
        return self.event_graph.get_session(session_id, limit)

    def get_related_topics(self, topic: str, limit: int = 5) -> List[str]:
        return self.topic_net.get_related_topics(topic, limit)

    def merge_sessions(self, by_topic: bool = True) -> None:
        """Placeholder: merge session knowledge into topic network."""
        logger.info("Session merge triggered (by_topic=%s)", by_topic)

    def _extract_topics(self, text: str) -> List[str]:
        """Simple keyword-based topic extraction."""
        import re

        keywords = [
            "memory",
            "graph",
            "search",
            "store",
            "index",
            "retrieval",
            "decay",
            "forgetting",
            "learning",
            "test",
            "bug",
            "fix",
            "feature",
            "release",
            "python",
            "typescript",
            "plugin",
            "bridge",
        ]
        found = []
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                found.append(kw)
        return found or ["general"]
