"""
Memory Compression Module for claw-mem v2.12.0

Active memory compression based on Focus and ProMem papers:
- Focus: Sawtooth pattern, autonomous triggering, Knowledge Block
- ProMem: Three-stage verification (extraction → completion → verification)

Phase 1-3 implementation (kept lightweight):
- Phase 1: Base architecture MemoryCompressor + KnowledgeBlock
- Phase 2: Rule-triggered compression (count/interval thresholds)
- Phase 3: Semantic deduplication (BM25 similarity)

Phase 4-5 pending (requires LLM):
- Phase 4: LLM extraction integration
- Phase 5: Self-verification
"""

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class CompressionLevel(Enum):
    """Compression level"""

    LIGHT = "light"  # Light compression (30%)
    MEDIUM = "medium"  # Medium compression (50%)
    AGGRESSIVE = "aggressive"  # Aggressive compression (70%)


class CompressionTrigger(Enum):
    """Compression trigger conditions"""

    MANUAL = "manual"  # Manual trigger
    MEMORY_COUNT = "memory_count"  # Memory count exceeds threshold
    TOKEN_ESTIMATE = "token_estimate"  # Token estimate exceeds threshold
    INTERVAL = "interval"  # Forced interval
    SESSION_END = "session_end"  # Session end


@dataclass
class CompressionConfig:
    """Compression configuration - combining Focus and ProMem design"""

    # Trigger conditions
    enabled: bool = True
    max_memories: int = 100  # Max memory count to trigger compression
    max_tokens: int = 10000  # Max token estimate to trigger compression
    compression_interval: int = 50  # Forced compression interval (operation count)

    # Deduplication config
    similarity_threshold: float = 0.8  # Similarity threshold (Phase 3)
    use_bm25_deduplication: bool = True  # Use BM25 deduplication

    # Knowledge Block config
    knowledge_block_enabled: bool = True
    knowledge_block_path: str = ".claw-mem/knowledge"
    max_knowledge_entries: int = 50  # Knowledge Block max entries

    # Compression level
    level: CompressionLevel = CompressionLevel.MEDIUM

    # Phase 4-5 (pending implementation)
    enable_self_verification: bool = False  # Not yet supported
    llm_extractor: Optional[Callable] = None  # Not yet supported

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_memories": self.max_memories,
            "max_tokens": self.max_tokens,
            "compression_interval": self.compression_interval,
            "similarity_threshold": self.similarity_threshold,
            "knowledge_block_enabled": self.knowledge_block_enabled,
            "level": self.level.value,
        }


@dataclass
class CompressionResult:
    """Compression result"""

    trigger: CompressionTrigger
    original_count: int
    compressed_count: int
    compression_ratio: float  # Compression ratio
    token_savings: float  # Token savings ratio

    # Retained memories (for debugging)
    preserved_memory_ids: List[str] = field(default_factory=list)
    removed_memory_ids: List[str] = field(default_factory=list)

    # Extracted key knowledge
    extracted_knowledge: List[str] = field(default_factory=list)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger.value,
            "original_count": self.original_count,
            "compressed_count": self.compressed_count,
            "compression_ratio": self.compression_ratio,
            "token_savings": self.token_savings,
            "preserved_count": len(self.preserved_memory_ids),
            "removed_count": len(self.removed_memory_ids),
            "extracted_knowledge_count": len(self.extracted_knowledge),
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


@dataclass
class KnowledgeEntry:
    """Knowledge Block entry"""

    key: str  # Knowledge key (e.g. "user_preference_python")
    value: str  # Knowledge value
    category: str  # Category: preference, decision, fact, skill
    source: str  # Source: compression, manual, extraction
    importance: float  # Importance 0-1
    memory_ids: List[str] = field(default_factory=list)  # Source memories
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "source": self.source,
            "importance": self.importance,
            "memory_ids": self.memory_ids,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            category=data["category"],
            source=data["source"],
            importance=data["importance"],
            memory_ids=data.get("memory_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            accessed_at=datetime.fromisoformat(data["accessed_at"]),
            access_count=data.get("access_count", 0),
        )


class KeyInformationExtractor:
    """
    Key information extractor (rule-based, no LLM)

    Extracts key information from text:
    - Decisions
    - Important facts
    - Tasks/goals
    - User preferences
    """

    # Pattern matching
    DECISION_PATTERNS = [
        r"(决定|决策|选择|确定|批准|同意|拒绝|否认|确定要)",
        r"(decided|decided to|agreed|accepted|rejected|chose|selected|will|should|must)",
    ]

    FACT_PATTERNS = [
        r"(事实|实际上|其实|已经|已知|确认|证明)",
        r"(fact|actually|known|already|confirmed|proven|true|realized)",
    ]

    TASK_PATTERNS = [
        r"(任务|目标|需要|完成|做|执行|下一步|计划)",
        r"(task|goal|need|complete|do|execute|action|next step|plan|intend)",
    ]

    PREFERENCE_PATTERNS = [
        r"(喜欢|偏爱|prefer|like|better|instead of|rather|enjoy)",
        r"(不喜欢|讨厌|dislike|hate|avoid|not fond of)",
    ]

    def __init__(self):
        self._decision_re = [re.compile(p, re.IGNORECASE) for p in self.DECISION_PATTERNS]
        self._fact_re = [re.compile(p, re.IGNORECASE) for p in self.FACT_PATTERNS]
        self._task_re = [re.compile(p, re.IGNORECASE) for p in self.TASK_PATTERNS]
        self._pref_re = [re.compile(p, re.IGNORECASE) for p in self.PREFERENCE_PATTERNS]

    def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract key information"""
        return {
            "decisions": self._extract_matches(text, self._decision_re),
            "facts": self._extract_matches(text, self._fact_re),
            "tasks": self._extract_matches(text, self._task_re),
            "preferences": self._extract_matches(text, self._pref_re),
        }

    def extract_categories(self, text: str) -> List[str]:
        """Extract information categories"""
        categories = []
        if self._has_match(text, self._decision_re):
            categories.append("decision")
        if self._has_match(text, self._fact_re):
            categories.append("fact")
        if self._has_match(text, self._task_re):
            categories.append("task")
        if self._has_match(text, self._pref_re):
            categories.append("preference")
        return categories if categories else ["general"]

    def _extract_matches(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Extract matching content"""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            matches.extend(found)
        return list(set(matches))

    def _has_match(self, text: str, patterns: List[re.Pattern]) -> bool:
        return any(p.search(text) for p in patterns)


class SemanticDeduplicator:
    """
    Semantic deduplicator (Phase 3)

    Uses BM25 similarity for deduplication
    """

    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self._extractor = KeyInformationExtractor()

    def deduplicate(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate memories

        Args:
            memories: List of memories

        Returns:
            Deduplicated list of memories
        """
        if not memories:
            return []

        # Sort by importance (retain high-importance ones)
        sorted_memories = sorted(memories, key=lambda m: m.get("importance", 0.5), reverse=True)

        unique = []
        _seen_content: Set[str] = set()
        for mem in sorted_memories:
            content = mem.get("content", "")
            if not content:
                continue

            # Simplified similarity check (based on key information overlap)
            is_duplicate = False
            content_lower = content.lower()

            for existing in unique:
                existing_content = existing.get("content", "").lower()
                if self._is_similar(content_lower, existing_content):
                    # Retain the one with higher importance
                    if mem.get("importance", 0) > existing.get("importance", 0):
                        unique.remove(existing)
                        unique.append(mem)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique.append(mem)

        return unique

    def _is_similar(self, text1: str, text2: str) -> bool:
        """Check whether two texts are similar (simplified version)"""
        # Extract key information
        info1 = self._extractor.extract(text1)
        info2 = self._extractor.extract(text2)

        # Calculate key information overlap
        all_info1 = set()
        all_info2 = set()

        for key in ["decisions", "facts", "tasks", "preferences"]:
            all_info1.update(info1.get(key, []))
            all_info2.update(info2.get(key, []))

        if not all_info1 or not all_info2:
            # If no key information extracted, use word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return False
            overlap = len(words1 & words2) / len(words1 | words2)
            return overlap >= self.threshold

        # Key information overlap
        overlap = len(all_info1 & all_info2) / len(all_info1 | all_info2)
        return overlap >= self.threshold


class KnowledgeBlock:
    """
    Persistent key learning zone (Focus design)

    Characteristics:
    - Always stays at the top of context
    - High-frequency access, low latency
    - Cross-session persistence
    """

    def __init__(self, storage_path: str, max_entries: int = 50):
        self.storage_path = storage_path
        self.max_entries = max_entries
        self._knowledge: Dict[str, KnowledgeEntry] = {}
        self._load()

    def add(
        self,
        key: str,
        value: str,
        category: str = "general",
        importance: float = 0.5,
        memory_ids: List[str] = None,
    ) -> None:
        """Add or update a knowledge entry"""
        if key in self._knowledge:
            # Update existing entry
            existing = self._knowledge[key]
            existing.value = value
            existing.importance = max(existing.importance, importance)
            existing.accessed_at = datetime.now()
            existing.access_count += 1
            if memory_ids:
                existing.memory_ids = list(set(existing.memory_ids + memory_ids))
        else:
            # New entry
            entry = KnowledgeEntry(
                key=key,
                value=value,
                category=category,
                source="compression",
                importance=importance,
                memory_ids=memory_ids or [],
            )
            self._knowledge[key] = entry

        # Maintain size limit
        self._trim()
        self._persist()

    def get(self, key: str) -> Optional[str]:
        """Get knowledge value"""
        if key in self._knowledge:
            entry = self._knowledge[key]
            entry.accessed_at = datetime.now()
            entry.access_count += 1
            self._persist()
            return entry.value
        return None

    def get_all(self, limit: int = 10) -> str:
        """Get all knowledge (formatted, for context injection)"""
        # Sort by access frequency and importance
        sorted_entries = sorted(
            self._knowledge.values(),
            key=lambda e: (e.access_count * 0.3 + e.importance * 0.7),
            reverse=True,
        )[:limit]

        if not sorted_entries:
            return ""

        lines = ["[Knowledge Block]"]
        for entry in sorted_entries:
            lines.append(f"- {entry.key}: {entry.value}")

        return "\n".join(lines)

    def get_dict(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get knowledge dictionary (for retrieval)"""
        sorted_entries = sorted(
            self._knowledge.values(),
            key=lambda e: (e.access_count * 0.3 + e.importance * 0.7),
            reverse=True,
        )[:limit]
        return [e.to_dict() for e in sorted_entries]

    def search(self, query: str) -> List[KnowledgeEntry]:
        """Search knowledge"""
        query_lower = query.lower()
        results = []
        for entry in self._knowledge.values():
            if query_lower in entry.key.lower() or query_lower in entry.value.lower():
                results.append(entry)
        return sorted(results, key=lambda e: e.importance, reverse=True)[:5]

    def _trim(self) -> None:
        """Maintain size limit, remove lowest priority entries"""
        if len(self._knowledge) <= self.max_entries:
            return

        sorted_entries = sorted(
            self._knowledge.values(),
            key=lambda e: (e.access_count * 0.3 + e.importance * 0.7),
            reverse=True,
        )

        # Keep top N
        self._knowledge = {e.key: e for e in sorted_entries[: self.max_entries]}

    def _load(self) -> None:
        """Load from disk"""
        path = self.storage_path
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    entry = KnowledgeEntry.from_dict(item)
                    self._knowledge[entry.key] = entry
        except Exception:
            pass

    def _persist(self) -> None:
        """Persist to disk"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = [e.to_dict() for e in self._knowledge.values()]
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class MemoryCompressorV2:
    """
    Memory Compressor V2 - combining Focus and ProMem design

    Phase 1: Base architecture
    Phase 2: Rule-triggered compression
    Phase 3: Semantic deduplication

    Workflow (sawtooth pattern):
    1. Determine whether compression is needed (should_compress)
    2. Extract key information (extract_key_facts)
    3. Semantic deduplication (deduplicate)
    4. Update Knowledge Block
    5. Return compression result
    """

    def __init__(
        self,
        config: Optional[CompressionConfig] = None,
        workspace_path: Optional[str] = None,
    ):
        self.config = config or CompressionConfig()
        self.workspace_path = workspace_path or "."

        # Internal state
        self.operation_count = 0
        self.last_compression_idx = 0
        self.compression_count = 0

        # Components
        self._extractor = KeyInformationExtractor()
        self._deduplicator = SemanticDeduplicator(threshold=self.config.similarity_threshold)

        # Knowledge Block
        self._knowledge_block: Optional[KnowledgeBlock] = None
        if self.config.knowledge_block_enabled:
            kb_path = os.path.join(self.workspace_path, self.config.knowledge_block_path)
            self._knowledge_block = KnowledgeBlock(kb_path, self.config.max_knowledge_entries)

    def should_compress(
        self, memory_count: int, token_estimate: int = 0, force: bool = False
    ) -> tuple[bool, Optional[CompressionTrigger]]:
        """
        Determine whether compression is needed (Phase 2)

        Returns:
            (whether compression is needed, trigger reason)
        """
        if not self.config.enabled or force:
            pass

        # Force trigger
        if force:
            return True, CompressionTrigger.MANUAL

        # Check each trigger condition
        if memory_count > self.config.max_memories:
            return True, CompressionTrigger.MEMORY_COUNT

        if token_estimate > self.config.max_tokens:
            return True, CompressionTrigger.TOKEN_ESTIMATE

        # Forced interval compression
        if (self.operation_count - self.last_compression_idx) >= self.config.compression_interval:
            return True, CompressionTrigger.INTERVAL

        return False, None

    def compress(
        self,
        memories: List[Dict[str, Any]],
        session_end: bool = False,
    ) -> CompressionResult:
        """
        Execute compression (Phase 1-3)

        Workflow:
        1. Extract key information
        2. Semantic deduplication
        3. Update Knowledge Block
        4. Return compression result
        """
        import time

        start_time = time.time()

        original_count = len(memories)
        if original_count == 0:
            return CompressionResult(
                trigger=CompressionTrigger.MANUAL,
                original_count=0,
                compressed_count=0,
                compression_ratio=0.0,
                token_savings=0.0,
            )

        # Phase 2: Determine trigger reason
        _, trigger = self.should_compress(original_count)
        if session_end:
            trigger = CompressionTrigger.SESSION_END
        trigger = trigger or CompressionTrigger.MANUAL

        # Phase 1: Extract key information (categorize)
        categorized_memories = self._categorize_memories(memories)

        # Phase 3: Semantic deduplication
        deduplicated = self._deduplicator.deduplicate(categorized_memories)

        # Update Knowledge Block
        extracted_knowledge = []
        if self._knowledge_block:
            extracted_knowledge = self._update_knowledge_block(deduplicated)

        # Calculate compression result
        compressed_count = len(deduplicated)
        compression_ratio = 1 - (compressed_count / original_count) if original_count > 0 else 0

        # Token savings estimate (assume average 100 tokens per memory)
        token_savings = compression_ratio

        # Update state
        self.last_compression_idx = self.operation_count
        self.compression_count += 1

        duration_ms = (time.time() - start_time) * 1000

        return CompressionResult(
            trigger=trigger,
            original_count=original_count,
            compressed_count=compressed_count,
            compression_ratio=compression_ratio,
            token_savings=token_savings,
            preserved_memory_ids=[m.get("id", "") for m in deduplicated],
            removed_memory_ids=[m.get("id", "") for m in memories if m not in deduplicated],
            extracted_knowledge=extracted_knowledge,
            duration_ms=duration_ms,
        )

    def _categorize_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize memories, add category labels"""
        categorized = []

        for mem in memories:
            content = mem.get("content", "")
            categories = self._extractor.extract_categories(content)

            # Calculate importance
            importance = 0.5
            if "decision" in categories:
                importance = 0.9
            elif "preference" in categories:
                importance = 0.8
            elif "task" in categories:
                importance = 0.7
            elif "fact" in categories:
                importance = 0.6

            # Merge importance
            existing_importance = mem.get("importance", 0.5)
            mem["importance"] = max(existing_importance, importance)
            mem["categories"] = categories

            categorized.append(mem)

        return categorized

    def _update_knowledge_block(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Update Knowledge Block"""
        if not self._knowledge_block:
            return []

        extracted = []

        for mem in memories:
            content = mem.get("content", "")
            memory_id = mem.get("id", "")
            importance = mem.get("importance", 0.5)
            categories = mem.get("categories", ["general"])

            # Generate key
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            key = f"{categories[0]}_{content_hash}"

            # Add to Knowledge Block
            self._knowledge_block.add(
                key=key,
                value=content[:200],  # Limit length
                category=categories[0],
                importance=importance,
                memory_ids=[memory_id],
            )

            extracted.append(key)

        return extracted

    def record_operation(self) -> None:
        """Record operation count"""
        self.operation_count += 1

    def get_knowledge_block(self) -> Optional[str]:
        """Get Knowledge Block content"""
        if self._knowledge_block:
            return self._knowledge_block.get_all()
        return None

    def search_knowledge(self, query: str) -> List[str]:
        """Search Knowledge Block"""
        if self._knowledge_block:
            entries = self._knowledge_block.search(query)
            return [e.value for e in entries]
        return []


# Global compressor instance
_compressor: Optional[MemoryCompressorV2] = None


def get_compressor(
    config: Optional[CompressionConfig] = None,
    workspace_path: Optional[str] = None,
) -> MemoryCompressorV2:
    """Get the compressor instance"""
    global _compressor
    if _compressor is None:
        _compressor = MemoryCompressorV2(config, workspace_path)
    return _compressor


def reset_compressor() -> None:
    """Reset the compressor"""
    global _compressor
    _compressor = None
