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
Three-Tier Memory Retrieval API

Implements cross-layer retrieval across:
- L1: Working Memory (current session context)
- L2: Short-term Memory (daily memory files)
- L3: Long-term Memory (MEMORY.md)

Performance targets:
- Retrieval latency: < 500ms (p95)
- Memory usage: < 100MB for index
- Cold start: < 2 seconds
"""

import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# Optional Jieba import for Chinese tokenization
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    jieba = None
    JIEBA_AVAILABLE = False


class MemoryLayer(Enum):
    """Memory layer enumeration"""
    L1 = "l1"  # Working Memory (current session)
    L2 = "l2"  # Short-term Memory (daily files)
    L3 = "l3"  # Long-term Memory (MEMORY.md)


@dataclass
class MemoryResult:
    """Memory search result"""
    memory_id: str
    content: str
    layer: MemoryLayer
    score: float
    source: str  # File path or "working_memory"
    timestamp: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    memory_type: str = "episodic"  # episodic/semantic/procedural

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "layer": self.layer.value,
            "score": self.score,
            "source": self.source,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "memory_type": self.memory_type,
        }


@dataclass
class SearchQuery:
    """Search query with metadata"""
    query: str
    layers: List[MemoryLayer] = field(default_factory=lambda: [MemoryLayer.L1, MemoryLayer.L2, MemoryLayer.L3])
    limit: int = 10
    memory_type: Optional[str] = None
    tags: Optional[List[str]] = None
    min_score: float = 0.1
    intent: Optional[str] = None  # Detected intent/topic
    session_id: Optional[str] = None


class IntentClassifier:
    """
    Simple intent/topic classifier for memory retrieval

    Extracts keywords and topics from queries to improve retrieval accuracy.
    """

    # Topic keywords mapping
    TOPIC_KEYWORDS = {
        "harness_engineering": ["harness", "engineering", "pillar", "agent", "architecture"],
        "project_neo": ["neo", "project neo", "multi-agent", "agent system"],
        "memory_system": ["memory", "recall", "retrieve", "search", "index"],
        "openclaw": ["openclaw", "claude", "assistant", "agent"],
        "technical": ["code", "api", "function", "class", "module", "implementation"],
        "personal": ["preference", "like", "dislike", "hobby", "interest"],
    }

    def __init__(self):
        """Initialize intent classifier"""
        self.jieba = jieba if JIEBA_AVAILABLE else None

    def classify(self, query: str) -> Tuple[Optional[str], List[str]]:
        """
        Classify query intent and extract keywords

        Args:
            query: Search query

        Returns:
            Tuple of (detected_intent, extracted_keywords)
        """
        keywords = self._extract_keywords(query)
        intent = self._detect_topic(keywords)

        return intent, keywords

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query

        Args:
            query: Search query

        Returns:
            List of keywords
        """
        # Tokenize based on language
        if self._contains_chinese(query):
            tokens = self._tokenize_chinese(query)
        else:
            tokens = self._tokenize_english(query)

        # Filter out stopwords and short tokens
        keywords = [t for t in tokens if len(t) > 1]

        return keywords

    def _detect_topic(self, keywords: List[str]) -> Optional[str]:
        """
        Detect topic from keywords

        Args:
            keywords: Extracted keywords

        Returns:
            Detected topic or None
        """
        keyword_set = set(k.lower() for k in keywords)

        best_match = None
        best_score = 0

        for topic, topic_keywords in self.TOPIC_KEYWORDS.items():
            matches = sum(1 for tk in topic_keywords if tk in keyword_set)
            score = matches / len(topic_keywords)

            if score > best_score and score >= 0.3:  # 30% match threshold
                best_score = score
                best_match = topic

        return best_match

    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def _tokenize_chinese(self, text: str) -> List[str]:
        """Tokenize Chinese text using Jieba or character-level"""
        if self.jieba is not None:
            try:
                return list(self.jieba.cut(text))
            except Exception:
                pass

        # Fallback to character-level
        return list(re.sub(r'[^\w\u4e00-\u9fff]', '', text))

    def _tokenize_english(self, text: str) -> List[str]:
        """Tokenize English text"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()


class ThreeTierRetriever:
    """
    Three-Tier Memory Retriever

    Provides unified search across L1 (Working), L2 (Short-term), and L3 (Long-term) memory layers.

    Features:
    - Cross-layer semantic search
    - Intent-based retrieval
    - Result deduplication and ranking
    - Performance logging
    """

    def __init__(self, workspace: Path):
        """
        Initialize Three-Tier Retriever

        Args:
            workspace: OpenClaw workspace path
        """
        from pathlib import Path as PathLib
        self.workspace = workspace if isinstance(workspace, PathLib) else PathLib(workspace)
        self.intent_classifier = IntentClassifier()

        # Storage paths
        self.memory_file = self.workspace / "MEMORY.md"  # L3
        self.memory_dir = self.workspace / "memory"  # L2

        # Performance metrics
        self._search_count = 0
        self._total_latency_ms = 0.0
        self._last_search_time: Optional[datetime] = None

    def search(self, query: str,
               layers: Optional[List[str]] = None,
               limit: int = 10,
               memory_type: Optional[str] = None,
               session_context: Optional[Dict] = None) -> List[MemoryResult]:
        """
        Cross-layer memory search

        Args:
            query: Search query
            layers: Layers to search ["l1", "l2", "l3"] (default: all)
            limit: Maximum results per layer
            memory_type: Filter by memory type (episodic/semantic/procedural)
            session_context: Current session context for L1 search

        Returns:
            List of MemoryResult objects, sorted by relevance
        """
        start_time = time.time()

        # Parse layer strings to enum
        layer_enums = []
        layers = layers or ["l1", "l2", "l3"]
        for layer_str in layers:
            if layer_str == "l1":
                layer_enums.append(MemoryLayer.L1)
            elif layer_str == "l2":
                layer_enums.append(MemoryLayer.L2)
            elif layer_str == "l3":
                layer_enums.append(MemoryLayer.L3)

        # Classify intent
        intent, keywords = self.intent_classifier.classify(query)

        # Create search query
        search_query = SearchQuery(
            query=query,
            layers=layer_enums,
            limit=limit,
            memory_type=memory_type,
            intent=intent,
        )

        # Search each layer
        all_results: List[MemoryResult] = []

        for layer in layer_enums:
            layer_results = self._search_layer(search_query, layer, session_context)
            all_results.extend(layer_results)

        # Deduplicate and rank
        ranked_results = self._rank_and_deduplicate(all_results, query)

        # Apply limit
        final_results = ranked_results[:limit]

        # Log performance
        latency_ms = (time.time() - start_time) * 1000
        self._log_performance(query, latency_ms, len(final_results))

        return final_results

    def _search_layer(self, query: SearchQuery, layer: MemoryLayer,
                      session_context: Optional[Dict] = None) -> List[MemoryResult]:
        """
        Search a specific memory layer

        Args:
            query: Search query
            layer: Memory layer to search
            session_context: Session context for L1

        Returns:
            List of MemoryResult objects
        """
        if layer == MemoryLayer.L1:
            return self._search_l1_working_memory(query, session_context)
        elif layer == MemoryLayer.L2:
            return self._search_l2_short_term(query)
        elif layer == MemoryLayer.L3:
            return self._search_l3_long_term(query)

        return []

    def _search_l1_working_memory(self, query: SearchQuery,
                                   session_context: Optional[Dict] = None) -> List[MemoryResult]:
        """
        Search L1: Working Memory (current session context)

        Args:
            query: Search query
            session_context: Session context containing working memories

        Returns:
            List of MemoryResult objects
        """
        if not session_context:
            return []

        working_memories = session_context.get("working_memory", [])
        results = []

        for memory in working_memories:
            content = memory.get("content", "")
            score = self._compute_relevance_score(query.query, content, query.intent)

            if score >= query.min_score:
                results.append(MemoryResult(
                    memory_id=memory.get("id", "l1_unknown"),
                    content=content,
                    layer=MemoryLayer.L1,
                    score=score,
                    source="working_memory",
                    timestamp=memory.get("timestamp"),
                    tags=memory.get("tags", []),
                    memory_type=memory.get("type", "episodic"),
                ))

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:query.limit]

    def _search_l2_short_term(self, query: SearchQuery) -> List[MemoryResult]:
        """
        Search L2: Short-term Memory (daily memory files)

        Args:
            query: Search query

        Returns:
            List of MemoryResult objects
        """
        results = []

        if not self.memory_dir.exists():
            return results

        # Find daily memory files (YYYY-MM-DD.md format)
        daily_files = sorted(
            self.memory_dir.glob("*.md"),
            key=lambda f: f.stem,
            reverse=True  # Most recent first
        )

        # Limit to recent files for performance (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_files = []
        for f in daily_files[:60]:  # Check at most 60 files
            try:
                file_date = datetime.strptime(f.stem, "%Y-%m-%d")
                if file_date >= cutoff_date:
                    recent_files.append(f)
            except ValueError:
                continue

        for file_path in recent_files:
            file_results = self._search_file(file_path, MemoryLayer.L2, query)
            results.extend(file_results)

        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:query.limit]

    def _search_l3_long_term(self, query: SearchQuery) -> List[MemoryResult]:
        """
        Search L3: Long-term Memory (MEMORY.md)

        Args:
            query: Search query

        Returns:
            List of MemoryResult objects
        """
        if not self.memory_file.exists():
            return []

        return self._search_file(self.memory_file, MemoryLayer.L3, query)

    def _search_file(self, file_path: Path, layer: MemoryLayer,
                     query: SearchQuery) -> List[MemoryResult]:
        """
        Search memories in a file

        Args:
            file_path: Path to memory file
            layer: Memory layer
            query: Search query

        Returns:
            List of MemoryResult objects
        """
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse memory entries
            memories = self._parse_memory_file(content, file_path)

            for memory in memories:
                # Filter by memory type if specified
                if query.memory_type and memory.get("type") != query.memory_type:
                    continue

                # Filter by tags if specified
                if query.tags:
                    memory_tags = memory.get("tags", [])
                    if not any(t in memory_tags for t in query.tags):
                        continue

                # Compute relevance score
                score = self._compute_relevance_score(query.query, memory.get("content", ""), query.intent)

                if score >= query.min_score:
                    results.append(MemoryResult(
                        memory_id=memory.get("id", f"{layer.value}_unknown"),
                        content=memory.get("content", ""),
                        layer=layer,
                        score=score,
                        source=str(file_path),
                        timestamp=memory.get("timestamp"),
                        tags=memory.get("tags", []),
                        memory_type=memory.get("type", "episodic"),
                    ))

        except Exception as e:
            print(f"Warning: Failed to search {file_path}: {e}")

        return results

    def _parse_memory_file(self, content: str, file_path: Path) -> List[Dict]:
        """
        Parse memory file content

        Args:
            content: File content
            file_path: Source file path

        Returns:
            List of memory dictionaries
        """
        memories = []
        current_meta = {}

        for line in content.split('\n'):
            line = line.strip()

            # Skip empty lines and headers
            if not line or line.startswith("#"):
                continue

            # Parse metadata comments
            if line.startswith("<!--") and line.endswith("-->"):
                meta_content = line[4:-3].strip()
                for item in meta_content.split(";"):
                    if ":" in item:
                        key, value = item.split(":", 1)
                        current_meta[key.strip()] = value.strip()

            # Parse memory content
            elif line.startswith("["):
                try:
                    end_timestamp = line.index("]")
                    timestamp = line[1:end_timestamp]
                    memory_content = line[end_timestamp+1:].strip()

                    # Parse tags
                    tags = []
                    if "tags" in current_meta:
                        tags = [t.strip() for t in current_meta["tags"].split(",")]

                    memories.append({
                        "id": current_meta.get("id"),
                        "timestamp": timestamp,
                        "content": memory_content,
                        "tags": tags,
                        "type": current_meta.get("type", "episodic"),
                        "source": str(file_path),
                    })

                    current_meta = {}  # Reset metadata
                except (ValueError, IndexError):
                    continue

        return memories

    def _compute_relevance_score(self, query: str, content: str,
                                  intent: Optional[str] = None) -> float:
        """
        Compute relevance score between query and content

        Args:
            query: Search query
            content: Memory content
            intent: Detected intent/topic

        Returns:
            Relevance score (0.0 - 1.0)
        """
        if not content:
            return 0.0

        query_lower = query.lower()
        content_lower = content.lower()

        # Exact match score
        exact_match = 1.0 if query_lower in content_lower else 0.0

        # Keyword match score
        query_keywords = set(query_lower.split())
        content_words = set(re.findall(r'\w+', content_lower))

        keyword_matches = len(query_keywords & content_words)
        keyword_score = keyword_matches / max(len(query_keywords), 1)

        # Intent boost
        intent_boost = 0.0
        if intent and intent in content_lower:
            intent_boost = 0.2

        # Combined score
        score = (0.5 * exact_match + 0.4 * keyword_score + 0.1 * intent_boost)

        # Normalize to 0-1 range
        return min(score, 1.0)

    def _rank_and_deduplicate(self, results: List[MemoryResult],
                               query: str) -> List[MemoryResult]:
        """
        Rank results and remove duplicates

        Args:
            results: Search results
            query: Original query

        Returns:
            Deduplicated and ranked results
        """
        # Deduplicate by content similarity
        seen_contents = set()
        unique_results = []

        for result in results:
            # Create content hash for deduplication
            content_hash = hash(result.content.lower().strip()[:100])

            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)

        # Sort by score
        unique_results.sort(key=lambda x: x.score, reverse=True)

        return unique_results

    def _log_performance(self, query: str, latency_ms: float, result_count: int) -> None:
        """
        Log search performance metrics

        Args:
            query: Search query
            latency_ms: Search latency in milliseconds
            result_count: Number of results returned
        """
        self._search_count += 1
        self._total_latency_ms += latency_ms
        self._last_search_time = datetime.now()

        avg_latency = self._total_latency_ms / self._search_count

        # Log slow searches
        if latency_ms > 500:
            print(f"Warning: Slow search detected: {latency_ms:.2f}ms for query: {query[:50]}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics

        Returns:
            Performance statistics dictionary
        """
        avg_latency = self._total_latency_ms / max(self._search_count, 1)

        return {
            "total_searches": self._search_count,
            "average_latency_ms": round(avg_latency, 2),
            "last_search_time": self._last_search_time.isoformat() if self._last_search_time else None,
            "performance_target_met": avg_latency < 500,
        }


class SessionStartupHook:
    """
    Session startup hook for automatic memory retrieval

    Automatically retrieves relevant memories when a new session starts.
    """

    def __init__(self, retriever: ThreeTierRetriever):
        """
        Initialize session startup hook

        Args:
            retriever: Three-tier retriever instance
        """
        self.retriever = retriever

    def on_session_start(self, session_id: str,
                         initial_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Called when a session starts

        Args:
            session_id: Session ID
            initial_context: Initial user context or greeting

        Returns:
            Retrieved memories for context injection
        """
        if not initial_context:
            # No context to retrieve on
            return {"memories": [], "intent": None}

        # Retrieve relevant memories
        memories = self.retriever.search(
            query=initial_context,
            layers=["l1", "l2", "l3"],
            limit=5,
        )

        # Get detected intent
        intent, _ = self.retriever.intent_classifier.classify(initial_context)

        return {
            "memories": [m.to_dict() for m in memories],
            "intent": intent,
            "session_id": session_id,
        }

    def format_context_for_prompt(self, memories: List[Dict]) -> str:
        """
        Format retrieved memories for prompt injection

        Args:
            memories: Retrieved memory dictionaries

        Returns:
            Formatted context string
        """
        if not memories:
            return ""

        lines = ["\n--- Retrieved Memories ---"]

        for i, memory in enumerate(memories, 1):
            layer = memory.get("layer", "unknown").upper()
            content = memory.get("content", "")
            source = memory.get("source", "")

            lines.append(f"[{layer}-{i}] {content}")
            if source and source != "working_memory":
                lines.append(f"  Source: {Path(source).name}")

        lines.append("--- End Retrieved Memories ---\n")

        return "\n".join(lines)


def search_memory(query: str,
                  layers: Optional[List[str]] = None,
                  limit: int = 10,
                  workspace: Optional[str] = None) -> List[Dict]:
    """
    Convenience function for cross-layer memory search

    Args:
        query: Search query
        layers: Layers to search ["l1", "l2", "l3"]
        limit: Maximum results
        workspace: OpenClaw workspace path (auto-detect if None)

    Returns:
        List of memory result dictionaries
    """
    # Auto-detect workspace
    if workspace is None:
        from ..config import ConfigDetector
        workspace = ConfigDetector.detect_workspace()

    workspace_path = Path(workspace).expanduser()
    retriever = ThreeTierRetriever(workspace_path)

    results = retriever.search(query, layers=layers, limit=limit)

    return [r.to_dict() for r in results]
