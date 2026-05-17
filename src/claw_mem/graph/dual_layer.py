# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
DualLayerMemory - Two-layer memory organization above the four-subgraph index.

Layer 1 - Event Progression Graph:
  Clusters memory nodes into "events" with temporal chains.

Layer 2 - Topic Associative Network:
  Groups events/nodes into "topics" with semantic links.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Tuple


@dataclass
class Event:
    """A cluster of related memory nodes forming a coherent activity."""

    event_id: str
    title: str
    description: str = ""
    node_ids: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    start_time: float = 0.0
    end_time: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "node_ids": self.node_ids,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        return cls(**{k: v for k, v in d.items()
                      if k in cls.__dataclass_fields__})


@dataclass
class Topic:
    """A semantic cluster of events/nodes sharing a common theme."""

    topic_id: str
    name: str
    description: str = ""
    node_ids: List[str] = field(default_factory=list)
    event_ids: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "description": self.description,
            "node_ids": self.node_ids,
            "event_ids": self.event_ids,
            "keywords": self.keywords,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Topic":
        return cls(**{k: v for k, v in d.items()
                      if k in cls.__dataclass_fields__})


class DualLayerMemory:
    """Two-layer memory structure on top of the four-subgraph index.

    Layer 1 - Event Progression Graph:
      - Clusters memory nodes into "events"
      - Maintains temporal chains between events (before/after)
      - Supports event chain backtracking

    Layer 2 - Topic Associative Network:
      - Groups events and nodes into "topics" by semantic theme
      - Maintains weighted associations between topics
      - Supports cross-session topic navigation
    """

    def __init__(self):
        self._events: Dict[str, Event] = {}
        self._topics: Dict[str, Topic] = {}
        self._event_chain: Dict[str, List[str]] = {}  # event_id → prev IDs
        self._topic_links: Dict[Tuple[str, str], float] = {}  # (t1,t2) → weight
        self._lock = Lock()

    # ── Layer 1: Event Progression Graph ──────────────────────────────

    def add_event(self, title: str, description: str = "",
                  node_ids: Optional[List[str]] = None,
                  session_id: Optional[str] = None,
                  tags: Optional[List[str]] = None) -> str:
        """Create a new event. Auto-links to the latest event in the same session.

        Args:
            title: Short event title.
            description: Optional description.
            node_ids: Associated memory node IDs.
            session_id: Owning OpenClaw session.
            tags: Labels for search/filtering.

        Returns:
            event_id (format: evt_<hex12>).
        """
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = datetime.now().timestamp()
        event = Event(
            event_id=event_id,
            title=title,
            description=description,
            node_ids=list(node_ids) if node_ids else [],
            session_id=session_id,
            start_time=now,
            tags=list(tags) if tags else [],
        )

        with self._lock:
            self._events[event_id] = event

            if session_id:
                prev = self._find_latest_event_in_session(session_id)
                if prev:
                    self._event_chain.setdefault(event_id, []).append(prev)

        return event_id

    def _find_latest_event_in_session(self, session_id: str) -> Optional[str]:
        """Find the most recent event in a session (by start_time)."""
        best_time = 0.0
        best_id = None
        for eid, evt in self._events.items():
            if evt.session_id == session_id:
                t = evt.end_time or evt.start_time
                if t > best_time:
                    best_time = t
                    best_id = eid
        return best_id

    def link_events(self, event1_id: str, event2_id: str) -> None:
        """Explicitly link two events bidirectionally."""
        with self._lock:
            chain = self._event_chain.setdefault(event1_id, [])
            if event2_id not in chain:
                chain.append(event2_id)
            chain = self._event_chain.setdefault(event2_id, [])
            if event1_id not in chain:
                chain.append(event1_id)

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get event details."""
        return self._events.get(event_id)

    def get_event_chain(self, event_id: str) -> List[Event]:
        """Get the event chain (predecessor event sequence).

        Args:
            event_id: Starting event.

        Returns:
            Chain of events ordered from newest to oldest.
        """
        visited: List[str] = []

        def _backtrack(eid: str):
            if eid in visited or eid not in self._events:
                return
            visited.append(eid)
            for prev_id in self._event_chain.get(eid, []):
                _backtrack(prev_id)

        with self._lock:
            _backtrack(event_id)

        return [self._events[eid] for eid in visited]

    def find_events_by_tags(self, tags: List[str]) -> List[Event]:
        """Find events matching any of the given tags."""
        results = []
        with self._lock:
            for evt in self._events.values():
                if any(t in evt.tags for t in tags):
                    results.append(evt)
        return results

    def find_events_by_session(self, session_id: str) -> List[Event]:
        """Find all events in a session."""
        results = []
        with self._lock:
            for evt in self._events.values():
                if evt.session_id == session_id:
                    results.append(evt)
        results.sort(key=lambda e: e.start_time)
        return results

    def event_count(self) -> int:
        with self._lock:
            return len(self._events)

    # ── Layer 2: Topic Associative Network ────────────────────────────

    def add_topic(self, name: str, description: str = "",
                  node_ids: Optional[List[str]] = None,
                  event_ids: Optional[List[str]] = None,
                  keywords: Optional[List[str]] = None) -> str:
        """Create a new topic.

        Args:
            name: Topic name.
            description: Optional description.
            node_ids: Associated node IDs.
            event_ids: Associated event IDs.
            keywords: Searchable keyword tags.

        Returns:
            topic_id (format: tpc_<hex12>).
        """
        topic_id = f"tpc_{uuid.uuid4().hex[:12]}"
        now = datetime.now().timestamp()
        topic = Topic(
            topic_id=topic_id,
            name=name,
            description=description,
            node_ids=list(node_ids) if node_ids else [],
            event_ids=list(event_ids) if event_ids else [],
            keywords=list(keywords) if keywords else [],
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._topics[topic_id] = topic
        return topic_id

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        return self._topics.get(topic_id)

    def link_topics(self, topic1_id: str, topic2_id: str,
                    weight: float = 0.5) -> None:
        """Link two topics with a symmetric weight."""
        with self._lock:
            self._topic_links[(topic1_id, topic2_id)] = weight
            self._topic_links[(topic2_id, topic1_id)] = weight

    def get_related_topics(self, topic_id: str,
                           min_weight: float = 0.3
                           ) -> List[Tuple[Topic, float]]:
        """Get related topics above the minimum weight threshold."""
        results: List[Tuple[Topic, float]] = []
        with self._lock:
            for (t1, t2), w in self._topic_links.items():
                if t1 == topic_id and w >= min_weight and t2 in self._topics:
                    results.append((self._topics[t2], w))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def search_by_keywords(self, keywords: List[str]) -> List[Topic]:
        """Search topics by keywords. Returns topics ordered by match count."""
        scored: List[Tuple[Topic, int]] = []
        kw_set = set(k.lower() for k in keywords)
        with self._lock:
            for topic in self._topics.values():
                score = len(kw_set & set(k.lower() for k in topic.keywords))
                if score > 0:
                    scored.append((topic, score))
        return [t for t, _ in sorted(scored, key=lambda x: x[1], reverse=True)]

    def topic_count(self) -> int:
        with self._lock:
            return len(self._topics)

    # ── Persistence ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "events": {
                    eid: evt.to_dict() for eid, evt in self._events.items()
                },
                "topics": {
                    tid: tpc.to_dict() for tid, tpc in self._topics.items()
                },
                "event_chain": {
                    k: v for k, v in self._event_chain.items()
                },
                "topic_links": {
                    f"{k[0]}||{k[1]}": v
                    for k, v in self._topic_links.items()
                },
            }

    @classmethod
    def from_dict(cls, d: dict) -> "DualLayerMemory":
        dm = cls()
        dm._events = {
            eid: Event.from_dict(ed)
            for eid, ed in d.get("events", {}).items()
        }
        dm._topics = {
            tid: Topic.from_dict(td)
            for tid, td in d.get("topics", {}).items()
        }
        dm._event_chain = {
            k: list(v) for k, v in d.get("event_chain", {}).items()
        }
        dm._topic_links = {}
        for k, v in d.get("topic_links", {}).items():
            t1, t2 = k.split("||", 1)
            dm._topic_links[(t1, t2)] = v
        return dm
