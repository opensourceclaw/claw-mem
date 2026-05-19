"""
Write-Time Gating

Source: Selective Memory paper
Core idea: Only store salient information, avoid memory redundancy

References:
    - Selective Memory: Learning what to remember
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class GatingResult:
    """Gating result"""

    stored: bool
    tier: str  # 'active' | 'cold'
    salience_score: float
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GatingFilterResult:
    """Gating filter result"""

    should_store: bool
    importance_score: float
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class GatingFilter:
    """Gating filter - decides whether to store based on importance score

    Uses ImportanceScorer to compute memory importance,
    decides whether to store to main storage based on threshold.

    Example:
        >>> from claw_mem.gating import GatingFilter
        >>> from claw_mem.importance import ImportanceScorer
        >>>
        >>> scorer = ImportanceScorer()
        >>> filter = GatingFilter(scorer=scorer, threshold=1.0)
        >>>
        >>> result = filter.should_store({
        ...     'memory_type': 'semantic',
        ...     'access_count': 5,
        ...     'content': 'important fact'
        ... })
        >>>
        >>> print(result.should_store)  # True/False
    """

    DEFAULT_THRESHOLD = 1.0  # Default threshold

    # Default weights for memory types
    TYPE_WEIGHTS = {
        "semantic": 0.5,
        "procedural": 0.3,
        "episodic": 0.0,
    }

    def __init__(
        self,
        scorer: Optional[Any] = None,
        threshold: float = DEFAULT_THRESHOLD,
        custom_score_func: Optional[Callable[[Dict], float]] = None,
    ):
        """
        Args:
            scorer: Importance scorer (ImportanceScorer)
            threshold: Storage threshold (default 1.0)
            custom_score_func: Custom scoring function
        """
        self.scorer = scorer
        self.threshold = threshold
        self.custom_score_func = custom_score_func

        # If no scorer is provided, use the built-in scoring
        if self.scorer is None and self.custom_score_func is None:
            self.scorer = _DefaultImportanceScorer()

    def should_store(self, memory: Dict[str, Any]) -> GatingFilterResult:
        """Determine whether to store

        Args:
            memory: Memory dict, containing:
                - memory_type: Memory type (semantic/procedural/episodic)
                - access_count: Access count
                - accessed_at: Last access time
                - content: Content
                - source: Source (user/agent/system)

        Returns:
            GatingFilterResult: Gating result
        """
        # Compute importance score
        if self.custom_score_func:
            score = self.custom_score_func(memory)
        elif self.scorer:
            score = self.scorer.calculate(memory).total_score
        else:
            # Default scoring
            score = self._default_score(memory)

        # Determine whether to store
        should_store = score >= self.threshold

        # Generate reason
        reason = self._generate_reason(memory, score, should_store)

        return GatingFilterResult(
            should_store=should_store,
            importance_score=score,
            reason=reason,
            metadata={
                "memory_type": memory.get("memory_type", "unknown"),
                "threshold": self.threshold,
            },
        )

    def _default_score(self, memory: Dict[str, Any]) -> float:
        """Default scoring logic"""
        score = 1.0  # Base score

        # Memory type weight
        mem_type = memory.get("memory_type", "episodic")
        score += self.TYPE_WEIGHTS.get(mem_type, 0.0)

        # Access frequency weight
        access_count = memory.get("access_count", 0)
        if access_count > 10:
            score += 0.3
        elif access_count > 5:
            score += 0.2
        elif access_count > 1:
            score += 0.1

        # Source weight
        source = memory.get("source", "system")
        if source == "user":
            score += 0.2
        elif source == "agent":
            score += 0.1

        return min(2.0, score)

    def _generate_reason(self, memory: Dict[str, Any], score: float, should_store: bool) -> str:
        """Generate decision reason"""
        mem_type = memory.get("memory_type", "unknown")
        source = memory.get("source", "unknown")

        if should_store:
            return f"High importance ({score:.2f} >= {self.threshold}): type={mem_type}, source={source}"
        else:
            return (
                f"Low importance ({score:.2f} < {self.threshold}): type={mem_type}, source={source}"
            )

    def set_threshold(self, threshold: float):
        """Set a new threshold"""
        self.threshold = max(0.0, min(2.0, threshold))

    def get_threshold(self) -> float:
        """Get current threshold"""
        return self.threshold


class _DefaultImportanceScorer:
    """Default importance scorer"""

    def calculate(self, memory: Dict[str, Any]) -> "MemoryImportance":
        """Compute importance"""
        # Simplified implementation
        score = 1.0
        mem_type = memory.get("memory_type") or "episodic"

        type_weights = {"semantic": 0.5, "procedural": 0.3, "episodic": 0.0}
        score += type_weights.get(mem_type, 0.0)

        access_count = memory.get("access_count") or 0
        if access_count > 10:
            score += 0.3
        elif access_count > 5:
            score += 0.2
        elif access_count > 1:
            score += 0.1

        return MemoryImportance(total_score=min(2.0, score))


class MemoryImportance:
    """Memory importance data structure"""

    def __init__(self, total_score: float = 1.0):
        self.total_score = total_score


class AdaptiveThreshold:
    """Adaptive threshold - dynamically adjusts based on memory count

    When memory count is high, raise the threshold to filter low-importance memories;
    When memory count is low, lower the threshold to retain more memories.

    Example:
        >>> from claw_mem.gating import AdaptiveThreshold
        >>>
        >>> adapter = AdaptiveThreshold(
        ...     base_threshold=1.0,
        ...     min_threshold=0.5,
        ...     max_threshold=1.5,
        ...     memory_capacity=1000
        ... )
        >>>
        >>> # Compute threshold based on current memory count
        >>> threshold = adapter.get_threshold(current_memory_count=500)
        >>> print(threshold)  # ~1.0
        >>>
        >>> threshold = adapter.get_threshold(current_memory_count=900)
        >>> print(threshold)  # ~1.3
    """

    def __init__(
        self,
        base_threshold: float = 1.0,
        min_threshold: float = 0.5,
        max_threshold: float = 1.5,
        memory_capacity: int = 1000,
        scale_factor: float = 0.5,
    ):
        """
        Args:
            base_threshold: Base threshold
            min_threshold: Minimum threshold
            max_threshold: Maximum threshold
            memory_capacity: Memory capacity reference value
            scale_factor: Scaling factor, controls the rate of threshold change
        """
        self.base_threshold = base_threshold
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.memory_capacity = memory_capacity
        self.scale_factor = scale_factor

    def get_threshold(self, current_memory_count: int) -> float:
        """Compute threshold based on current memory count

        Args:
            current_memory_count: Current memory count

        Returns:
            float: Dynamically computed threshold
        """
        # Compute usage ratio
        usage_ratio = current_memory_count / self.memory_capacity

        # Use sigmoid-like function for smooth transition
        # When usage_ratio = 0.5, threshold = base_threshold
        # When usage_ratio approaches 0, threshold approaches min_threshold
        # When usage_ratio approaches 1, threshold approaches max_threshold

        # Adjust offset so that base_threshold is at usage_ratio=0.5
        adjusted = (usage_ratio - 0.5) * self.scale_factor * 2
        threshold = self.base_threshold + adjusted

        # Clamp within min/max range
        return max(self.min_threshold, min(self.max_threshold, threshold))

    def get_stats(self, current_memory_count: int) -> Dict[str, Any]:
        """Get statistics

        Args:
            current_memory_count: Current memory count

        Returns:
            Dict: Statistics
        """
        threshold = self.get_threshold(current_memory_count)
        return {
            "current_count": current_memory_count,
            "capacity": self.memory_capacity,
            "usage_ratio": current_memory_count / self.memory_capacity,
            "current_threshold": threshold,
            "base_threshold": self.base_threshold,
            "min_threshold": self.min_threshold,
            "max_threshold": self.max_threshold,
        }

    def reset(self):
        """Reset to base threshold"""
        return self.base_threshold


class InMemoryStorage:
    """Active memory storage"""

    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def store(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Store to active memory"""
        stored_item = {**item, "_stored_at": datetime.now().isoformat(), "_tier": "active"}
        self._items.append(stored_item)
        return stored_item

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a memory item"""
        for item in self._items:
            if item.get("id") == key or item.get("content", "").startswith(key):
                return item
        return None

    def count(self) -> int:
        """Return storage count"""
        return len(self._items)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all memories"""
        return self._items.copy()

    def clear(self):
        """Clear storage"""
        self._items.clear()


class DiskStorage:
    """Cold storage (disk)"""

    def __init__(self, storage_path: str = "/tmp/claw-mem-cold"):
        import os

        self._storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._count = 0

    def archive(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Archive to cold storage"""
        import json

        stored_item = {**item, "_stored_at": datetime.now().isoformat(), "_tier": "cold"}

        # Use timestamp as filename
        filename = f"{self._storage_path}/{int(time.time() * 1000)}.json"
        with open(filename, "w") as f:
            json.dump(stored_item, f)

        self._count += 1
        return stored_item

    def count(self) -> int:
        """Return archive count"""
        return self._count

    def list_all(self) -> List[Dict[str, Any]]:
        """List all archives"""
        import json
        import os

        items = []
        for filename in os.listdir(self._storage_path):
            if filename.endswith(".json"):
                with open(f"{self._storage_path}/{filename}") as f:
                    items.append(json.load(f))
        return items


class VersionChain:
    """Version chain management"""

    def __init__(self):
        self._chain: List[Dict[str, Any]] = []

    def append(self, item: Dict[str, Any]):
        """Append version"""
        self._chain.append({**item, "_version": len(self._chain)})

    def get(self, index: int) -> Optional[Dict[str, Any]]:
        """Get specified version"""
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def latest(self) -> Optional[Dict[str, Any]]:
        """Get latest version"""
        return self._chain[-1] if self._chain else None

    def __len__(self) -> int:
        return len(self._chain)

    def clear(self):
        """Clear version chain"""
        self._chain.clear()


class WriteTimeGating:
    """Write-time gating - only store salient information

    Core features:
    1. Salience scoring
    2. Hot/cold storage tiering
    3. Version chain management

    Example:
        >>> gating = WriteTimeGating(threshold=0.6)
        >>> result = gating.write({
        ...     'content': 'important decision...',
        ...     'source': 'user',
        ...     'context': {...}
        ... })
        >>> print(result.stored, result.tier)
        True 'active'
    """

    def __init__(
        self,
        threshold: float = 0.6,
        active_memory: Optional[Any] = None,
        cold_storage: Optional[Any] = None,
    ):
        """
        Args:
            threshold: Salience threshold, default 0.6
            active_memory: Active memory storage
            cold_storage: Cold storage
        """
        self.threshold = threshold
        self.active_memory = active_memory or InMemoryStorage()
        self.cold_storage = cold_storage or DiskStorage()
        self.salience_scorer = SalienceScorer()
        self.version_chain = VersionChain()

    def write(self, item: Dict[str, Any]) -> GatingResult:
        """Write a memory item

        Args:
            item: Memory item, containing:
                - content: Content
                - source: Source (user/agent/system)
                - context: Context
                - metadata: Metadata

        Returns:
            GatingResult: Gating result
        """
        start_time = time.time()

        # 1. Compute salience score
        salience = self.salience_scorer.compute(item)

        # 2. Determine storage tier
        if salience >= self.threshold:
            # High salience -> active memory
            stored_item = self.active_memory.store(item)
            tier = "active"
            stored = True
            reason = f"High salience ({salience:.2f} >= {self.threshold})"
        else:
            # Low salience -> cold storage
            stored_item = self.cold_storage.archive(item)
            tier = "cold"
            stored = True
            reason = f"Low salience ({salience:.2f} < {self.threshold})"

        # 3. Update version chain
        self.version_chain.append(stored_item)

        _elapsed_ms = (time.time() - start_time) * 1000
        return GatingResult(stored=stored, tier=tier, salience_score=salience, reason=reason)

    def should_store(self, item: Dict[str, Any]) -> bool:
        """Determine whether to store (pre-check)

        Args:
            item: Memory item

        Returns:
            bool: Whether to store to active memory
        """
        salience = self.salience_scorer.compute(item)
        return salience >= self.threshold

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            "active_count": self.active_memory.count(),
            "cold_count": self.cold_storage.count(),
            "version_chain_length": len(self.version_chain),
            "threshold": self.threshold,
        }

    def promote(self, item_id: str, target_tier: str = "active") -> bool:
        """Promote memory item to a higher tier

        Args:
            item_id: Memory item ID
            target_tier: Target tier

        Returns:
            bool: Whether successful
        """
        # Read from cold storage
        cold_items = self.cold_storage.list_all()
        for item in cold_items:
            if item.get("id") == item_id or item.get("content", "").startswith(item_id):
                # Move to active memory
                self.active_memory.store(item)
                return True
        return False


class SalienceScorer:
    """Salience scorer

    Source: Selective Memory paper
    Core algorithm: Multi-dimensional weighted scoring

    Scoring dimensions:
    1. Source reputation - weight 0.4
    2. Novelty - weight 0.3
    3. Reliability - weight 0.3
    """

    # Source reputation weights
    SOURCE_REPUTATION = {
        "user": 1.0,  # User input has highest priority
        "agent": 0.8,  # Agent-generated information
        "system": 0.6,  # System information
        "external": 0.4,  # External sources
    }

    def __init__(self, weights: Dict[str, float] = None, novelty_window: int = 100):
        """
        Args:
            weights: Weights for each dimension, defaults:
                - source_reputation: 0.4
                - novelty: 0.3
                - reliability: 0.3
            novelty_window: Novelty computation window size
        """
        self.weights = weights or {"source_reputation": 0.4, "novelty": 0.3, "reliability": 0.3}
        self.novelty_window = novelty_window
        self.recent_items: List[str] = []

    def compute(self, item: Dict[str, Any]) -> float:
        """Compute salience score

        Args:
            item: Memory item

        Returns:
            float: Salience score (0.0 ~ 1.0)
        """
        # 1. Source reputation (40%)
        source_score = self._source_reputation(item.get("source", "external"))

        # 2. Novelty (30%)
        novelty_score = self._novelty(item.get("content", ""))

        # 3. Reliability (30%)
        reliability_score = self._reliability(item)

        # Weighted average
        salience = (
            self.weights["source_reputation"] * source_score
            + self.weights["novelty"] * novelty_score
            + self.weights["reliability"] * reliability_score
        )

        # Update recent records
        self._update_recent(item.get("content", ""))

        return salience

    def _source_reputation(self, source: str) -> float:
        """Source reputation scoring"""
        return self.SOURCE_REPUTATION.get(source, 0.5)

    def _novelty(self, content: str) -> float:
        """Novelty scoring

        Based on difference between content and recent records
        """
        if not self.recent_items:
            return 1.0  # First item has highest novelty

        # Simple implementation: compute similarity with recent content
        # Actual implementation could use a more sophisticated algorithm
        similarities = [self._simple_similarity(content, recent) for recent in self.recent_items]

        avg_similarity = sum(similarities) / len(similarities)

        # Lower similarity means higher novelty
        novelty = 1.0 - avg_similarity

        return max(0.0, min(1.0, novelty))

    def _reliability(self, item: Dict[str, Any]) -> float:
        """Reliability scoring

        Based on source, validation status, and context completeness
        """
        score = 0.5  # Base score

        # Source bonus
        source = item.get("source", "")
        if source in ["user", "agent"]:
            score += 0.2

        # Validation status bonus
        if item.get("verified", False):
            score += 0.2

        # Context completeness bonus
        context = item.get("context", {})
        if context and len(context) > 0:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple similarity computation (based on word overlap)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _update_recent(self, content: str):
        """Update recent records"""
        self.recent_items.append(content)

        # Maintain window size
        if len(self.recent_items) > self.novelty_window:
            self.recent_items.pop(0)
