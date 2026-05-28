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
Dreaming Engine — Light Phase (Signal Ingestor | v4.12.0)

Reads recent episodic memories, computes basic signal metrics,
deduplicates against existing semantic memories, and stages
candidates for deep scoring.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import DreamingConfig


@dataclass
class Signal:
    """A staged memory signal awaiting deep scoring.

    Attributes:
        memory_id: Source memory ID.
        content: Memory content text.
        memory_type: Type (episodic, semantic, etc.).
        recall_count: How many times this signal has been recalled.
        unique_queries: Set of distinct queries that matched this content.
        relevance_scores: List of relevance scores from prior retrievals.
        tags: Associated tags.
        timestamp: ISO timestamp string.
    """

    memory_id: str
    content: str
    memory_type: str = "episodic"
    recall_count: int = 1
    unique_queries: int = 0
    relevance_scores: List[float] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "recall_count": self.recall_count,
            "unique_queries": self.unique_queries,
            "relevance_scores": self.relevance_scores,
            "tags": self.tags,
            "timestamp": self.timestamp,
        }


class SignalIngestor:
    """Read recent episodic memories and stage signals for the dreaming pipeline.

    Deduplicates against existing semantic memories via substring matching.
    """

    def __init__(self, memory_manager: Any, config: Optional[DreamingConfig] = None):
        from .config import DreamingConfig

        self._mm = memory_manager
        self._config = config or DreamingConfig()
        self._staged: List[Signal] = []

    # ── public API ─────────────────────────────────────────────────

    def ingest(self) -> int:
        """Read recent episodic memories, deduplicate, and stage signals.

        Returns:
            Number of signals staged.
        """
        episodic = self._mm.episodic.get_recent(self._config.max_staged)
        existing_semantic = self._mm.semantic.get_all()

        # Collect existing semantic content for substring dedup
        semantic_texts = [m.get("content", "") for m in existing_semantic]

        # Count query occurrences per content
        content_counts: Counter = Counter()
        content_queries: Dict[str, set] = {}

        for mem in episodic:
            content = mem.get("content", "")
            if not content:
                continue
            content_counts[content] += 1
            content_queries.setdefault(content, set())

            # Extract distinct queries from tags or metadata
            queries = mem.get("tags", [])
            if queries:
                content_queries[content].update(queries)

        self._staged.clear()

        for mem in episodic:
            content = mem.get("content", "")
            if not content:
                continue

            # Deduplicate: skip if substring match against any semantic memory
            if any(content in st or st in content for st in semantic_texts):
                continue

            signal = Signal(
                memory_id=mem.get("id", ""),
                content=content,
                memory_type=mem.get("type", "episodic"),
                recall_count=content_counts[content],
                unique_queries=len(content_queries.get(content, set())),
                relevance_scores=[0.5],  # baseline
                tags=mem.get("tags", []),
                timestamp=mem.get("timestamp", ""),
            )
            self._staged.append(signal)

        return len(self._staged)

    def get_staged(self) -> List[Dict[str, Any]]:
        """Get all staged signals as dicts."""
        return [s.to_dict() for s in self._staged]

    def clear_staged(self) -> None:
        """Clear all staged signals."""
        self._staged.clear()
