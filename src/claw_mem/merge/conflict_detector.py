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
ConflictDetector (F3 · v4.7.0)

Detects contradictory or inconsistent semantic memories and resolves them
by keeping the higher-confidence version with optional LLM arbitration.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..memory_manager import MemoryManager
    from ..llm_provider import LLMProvider
    from ..retrieval.embedding_service import EmbeddingService

from .semantic_merger import _cosine_similarity


# ── data types ─────────────────────────────────────────────────────────

@dataclass
class ConflictReport:
    """A detected conflict between two memory records."""
    conflict_type: str            # "entity", "timeline", "semantic"
    memory_id_a: str
    memory_id_b: str
    content_a: str
    content_b: str
    description: str = ""
    similarity: float = 0.0
    resolved: bool = False
    resolution: Optional["ConflictResolution"] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "memory_id_a": self.memory_id_a,
            "memory_id_b": self.memory_id_b,
            "content_a": self.content_a,
            "content_b": self.content_b,
            "description": self.description,
            "similarity": self.similarity,
            "resolved": self.resolved,
            "resolution": self.resolution.to_dict() if self.resolution else None,
        }


@dataclass
class ConflictResolution:
    """Resolution of a detected conflict."""
    action: str                  # "keep_a", "keep_b", "merge", "manual"
    winner_id: str = ""          # Which memory to keep (if keep_*)
    merged_content: str = ""     # Merged text (if action=merge)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "winner_id": self.winner_id,
            "merged_content": self.merged_content,
            "reasoning": self.reasoning,
        }


# ── LLM prompts ────────────────────────────────────────────────────────

_CONFLICT_CHECK_PROMPT = (
    "Are these two statements contradictory or inconsistent? "
    "Answer YES or NO, then explain briefly.\n\n"
    "Statement A: {a}\nStatement B: {b}"
)

_CONFLICT_RESOLVE_PROMPT = (
    "Choose the correct version from two conflicting memories. "
    "Pick the one that is more specific, more recent, or more authoritative. "
    "Reply with 'A', 'B', or 'MERGE'. If MERGE, provide the merged text.\n\n"
    "Memory A: {a}\nMemory B: {b}\n\nAnswer:"
)

# ── entity extraction helpers ──────────────────────────────────────────

_ENTITY_PATTERNS = [
    re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'),       # Proper names
    re.compile(r'@(\w+)'),                                       # @mentions
    re.compile(r'(?:city|country|company|person|project)\s*[:=]\s*(\S+)', re.I),  # key:value
]


def _extract_entities(text: str) -> List[str]:
    """Extract candidate entity names from text using simple heuristics."""
    entities: List[str] = []
    for pattern in _ENTITY_PATTERNS:
        for match in pattern.findall(text):
            name = match.strip().lower()
            if len(name) >= 2 and name not in entities:
                entities.append(name)
    return entities


def _extract_attributes(text: str) -> Dict[str, str]:
    """Extract attribute key-value pairs (e.g., 'age: 30', 'location: Beijing')."""
    attr_pattern = re.compile(r'(\w+)\s*[:=]\s*([^,;.\n]+)', re.I)
    attrs: Dict[str, str] = {}
    for match in attr_pattern.findall(text):
        key = match[0].strip().lower()
        val = match[1].strip()
        attrs[key] = val
    return attrs


# ── ConflictDetector ───────────────────────────────────────────────────

class ConflictDetector:
    """Detects and resolves contradictory semantic memories.

    Three detection strategies:
      1. Entity attribute conflicts: same entity, different attribute values
      2. Timeline conflicts: event time order inconsistencies
      3. Semantic conflicts: highly similar (>0.7) but contradictory content
    """

    def __init__(
        self,
        manager: "MemoryManager",
        llm_provider: "LLMProvider",
        embedding_service: "EmbeddingService" = None,
        sim_threshold: float = 0.7,
    ):
        self.manager = manager
        self.llm_provider = llm_provider
        self._embedding_service = embedding_service
        self.sim_threshold = sim_threshold
        self._conflict_history: List[ConflictReport] = []

    @property
    def embedding_service(self) -> "EmbeddingService":
        if self._embedding_service is None:
            from ..retrieval.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    # ── detection ──────────────────────────────────────────────────────

    def detect_conflicts(self) -> List[ConflictReport]:
        """Run all three conflict detection strategies.

        Returns a (possibly empty) list of ConflictReport objects.
        """
        storage = self.manager.semantic
        all_memories = storage.get_all()
        active = [m for m in all_memories
                  if m.get("id") and m.get("content")
                  and m.get("metadata", {}).get("deprecated") not in ("true", "True", "1")]

        if len(active) < 2:
            return []

        conflicts: List[ConflictReport] = []

        # Strategy 1: entity attribute conflicts
        conflicts.extend(self._detect_entity_conflicts(active))

        # Strategy 2: timeline conflicts
        conflicts.extend(self._detect_timeline_conflicts(active))

        # Strategy 3: semantic conflicts (high similarity, contradictory)
        conflicts.extend(self._detect_semantic_conflicts(active))

        self._conflict_history.extend(conflicts)
        return conflicts

    def _detect_entity_conflicts(self, active: List[Dict[str, Any]]) -> List[ConflictReport]:
        """Detect same-entity, different-attribute-value conflicts."""
        conflicts: List[ConflictReport] = []

        # Index memories by entities they mention
        entity_index: Dict[str, List[Dict[str, Any]]] = {}
        for mem in active:
            for entity in _extract_entities(mem["content"]):
                entity_index.setdefault(entity, []).append(mem)

        seen_pairs: set = set()
        for entity, mems in entity_index.items():
            if len(mems) < 2:
                continue
            for i in range(len(mems)):
                for j in range(i + 1, len(mems)):
                    mid_a, mid_b = mems[i]["id"], mems[j]["id"]
                    pair_key = tuple(sorted([mid_a, mid_b]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    attrs_a = _extract_attributes(mems[i]["content"])
                    attrs_b = _extract_attributes(mems[j]["content"])
                    conflicts_found = []
                    for key in set(attrs_a) & set(attrs_b):
                        if attrs_a[key].lower() != attrs_b[key].lower():
                            conflicts_found.append(f"{key}: {attrs_a[key]} vs {attrs_b[key]}")

                    if conflicts_found:
                        conflicts.append(ConflictReport(
                            conflict_type="entity",
                            memory_id_a=mid_a,
                            memory_id_b=mid_b,
                            content_a=mems[i]["content"],
                            content_b=mems[j]["content"],
                            description=f"Entity '{entity}' has conflicting attributes: "
                                        f"{', '.join(conflicts_found)}",
                        ))
        return conflicts

    def _detect_timeline_conflicts(self, active: List[Dict[str, Any]]) -> List[ConflictReport]:
        """Detect timeline inconsistencies (event A happens before B but described differently)."""
        conflicts: List[ConflictReport] = []

        # Find memories with temporal expressions
        time_pattern = re.compile(
            r'(?:in|at|on|during|since|before|after|until|from|by)\s+'
            r'(?:the\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
            r'\s+\d{2,4}|\d{2,4}[-\/]\d{1,2}[-\/]\d{1,2}', re.I
        )

        timed_memories = [m for m in active if time_pattern.search(m["content"])]
        if len(timed_memories) < 2:
            return conflicts

        # Compare pairs with temporal references via LLM
        seen_pairs: set = set()
        for i in range(len(timed_memories)):
            for j in range(i + 1, len(timed_memories)):
                mid_a, mid_b = timed_memories[i]["id"], timed_memories[j]["id"]
                pair_key = tuple(sorted([mid_a, mid_b]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                prompt = _CONFLICT_CHECK_PROMPT.format(
                    a=timed_memories[i]["content"],
                    b=timed_memories[j]["content"],
                )
                response = self.llm_provider.generate(prompt, max_tokens=64)
                if response.upper().startswith("YES"):
                    conflicts.append(ConflictReport(
                        conflict_type="timeline",
                        memory_id_a=mid_a,
                        memory_id_b=mid_b,
                        content_a=timed_memories[i]["content"],
                        content_b=timed_memories[j]["content"],
                        description=response,
                    ))

        return conflicts

    def _detect_semantic_conflicts(self, active: List[Dict[str, Any]]) -> List[ConflictReport]:
        """Detect highly similar but contradictory memories via embeddings + LLM."""
        conflicts: List[ConflictReport] = []
        if len(active) < 2:
            return conflicts

        texts = [m["content"] for m in active]
        try:
            embeddings = self.embedding_service.encode(texts)
        except Exception:
            return conflicts

        n = len(active)
        seen_pairs: set = set()
        for i in range(n):
            for j in range(i + 1, n):
                mid_a, mid_b = active[i]["id"], active[j]["id"]
                pair_key = tuple(sorted([mid_a, mid_b]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                sim = _cosine_similarity(embeddings[i], embeddings[j])
                if sim < self.sim_threshold:
                    continue

                # High similarity — check for contradiction via LLM
                prompt = _CONFLICT_CHECK_PROMPT.format(
                    a=active[i]["content"],
                    b=active[j]["content"],
                )
                response = self.llm_provider.generate(prompt, max_tokens=64)
                if response.upper().startswith("YES"):
                    conflicts.append(ConflictReport(
                        conflict_type="semantic",
                        memory_id_a=mid_a,
                        memory_id_b=mid_b,
                        content_a=active[i]["content"],
                        content_b=active[j]["content"],
                        description=response,
                        similarity=sim,
                    ))

        return conflicts

    # ── resolution ─────────────────────────────────────────────────────

    def resolve_conflict(self, conflict: ConflictReport) -> ConflictResolution:
        """Resolve a single conflict via LLM arbitration.

        Strategy: keep the higher-confidence version, or merge if equally valid.
        """
        prompt = _CONFLICT_RESOLVE_PROMPT.format(
            a=conflict.content_a, b=conflict.content_b
        )
        answer = self.llm_provider.generate(prompt, max_tokens=128)

        if answer.upper().startswith("A"):
            resolution = ConflictResolution(
                action="keep_a",
                winner_id=conflict.memory_id_a,
                reasoning=answer,
            )
        elif answer.upper().startswith("B"):
            resolution = ConflictResolution(
                action="keep_b",
                winner_id=conflict.memory_id_b,
                reasoning=answer,
            )
        else:
            # Default to merge — try to combine
            merged = self.llm_provider.generate(
                f"Combine these two statements into one accurate statement. "
                f"Resolve any contradictions by keeping the more specific version.\n\n"
                f"A: {conflict.content_a}\nB: {conflict.content_b}\n\nCombined:",
                max_tokens=256,
            )
            resolution = ConflictResolution(
                action="merge",
                merged_content=merged or conflict.content_a,
                reasoning=answer,
            )

        conflict.resolved = True
        conflict.resolution = resolution
        return resolution

    # ── full cycle ─────────────────────────────────────────────────────

    def run_cycle(self) -> Dict[str, Any]:
        """Run a full conflict detection and resolution cycle.

        Returns stats dict.
        """
        t0 = time.monotonic()
        conflicts = self.detect_conflicts()

        resolved_count = 0
        for conflict in conflicts:
            try:
                self.resolve_conflict(conflict)
                resolved_count += 1
            except Exception:
                pass

        duration = round((time.monotonic() - t0) * 1000, 1)

        return {
            "conflicts_detected": len(conflicts),
            "conflicts_resolved": resolved_count,
            "by_type": {
                "entity": sum(1 for c in conflicts if c.conflict_type == "entity"),
                "timeline": sum(1 for c in conflicts if c.conflict_type == "timeline"),
                "semantic": sum(1 for c in conflicts if c.conflict_type == "semantic"),
            },
            "duration_ms": duration,
        }

    def get_history(self) -> List[ConflictReport]:
        """Return the full conflict detection history."""
        return list(self._conflict_history)

    def clear_history(self) -> None:
        """Clear the conflict history."""
        self._conflict_history.clear()

    def __repr__(self) -> str:
        return f"ConflictDetector(threshold={self.sim_threshold})"
