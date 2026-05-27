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

"""F1: MemoryInjector + InjectorResult (v4.9.0 context control plane).

Five-stage injection pipeline between retrieval and context formatting:

  1. Confidence gate     – ConfidenceGate.filter() drops low-confidence memories
  2. Relevance threshold – score-based minimum relevance filter
  3. Diversity dedup     – Jaccard similarity deduplication (no embeddings needed)
  4. Sort                – recency + relevance composite scoring
  5. Token budget        – truncate to fit within max token budget
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..context_injection import estimate_tokens


# ── word-level Jaccard similarity (no external deps) ──────────────────

def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Word-level Jaccard similarity with CJK character awareness.

    CJK characters (U+4E00-U+9FFF) are treated as individual tokens;
    ASCII word segments are split on non-alphanumeric boundaries and
    lowercased.
    """
    def _tokenize(text: str) -> set:
        tokens: set = set()
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if '\u4e00' <= ch <= '\u9fff':
                tokens.add(ch)
                i += 1
            elif ch.isalnum():
                j = i
                while (j < n and text[j].isalnum()
                       and not ('\u4e00' <= text[j] <= '\u9fff')):
                    j += 1
                tokens.add(text[i:j].lower())
                i = j
            else:
                i += 1
        return tokens

    set_a = _tokenize(text_a)
    set_b = _tokenize(text_b)

    if not set_a or not set_b:
        return 0.0

    return len(set_a & set_b) / len(set_a | set_b)


# ── data classes ──────────────────────────────────────────────────────

@dataclass
class InjectorResult:
    """Result of MemoryInjector.refine() with full pipeline metadata."""

    refined_memories: List[Dict[str, Any]]
    total_candidates: int
    total_removed: int
    total_tokens: int
    max_allowed: int
    diversity_removed: int = 0
    threshold_removed: int = 0
    budget_exceeded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> int:
        return len(self.refined_memories)


# ── MemoryInjector ────────────────────────────────────────────────────

class MemoryInjector:
    """Five-stage injection pipeline with token budget and diversity control.

    Usage::

        injector = MemoryInjector(confidence_gate=gate, max_tokens=2000)
        result = injector.refine(memories)

        # Use result.refined_memories for context injection
        # Inspect result.metadata for stage-level diagnostics
    """

    def __init__(
        self,
        confidence_gate: Any = None,
        max_tokens: int = 2000,
        diversity_threshold: float = 0.8,
        relevance_threshold: float = 0.3,
        recency_weight: float = 0.4,
        relevance_weight: float = 0.6,
        enable_confidence_gate: bool = True,
    ):
        self.confidence_gate = confidence_gate
        self.max_tokens = max_tokens
        self.diversity_threshold = diversity_threshold
        self.relevance_threshold = relevance_threshold
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        self.enable_confidence_gate = enable_confidence_gate

    # ── public API ─────────────────────────────────────────────────────

    def refine(self, memories: List[Dict]) -> InjectorResult:
        """Run 5-stage injection pipeline and return result with metadata."""
        total = len(memories)
        stages: List[Dict] = []
        current = list(memories)  # shallow copy – we replace the list each stage

        # Stage 1: Confidence gate
        removed_conf = 0
        if self.enable_confidence_gate and self.confidence_gate:
            before = len(current)
            current = self.confidence_gate.filter(current)
            removed_conf = before - len(current)
            stages.append({
                "name": "confidence_gate",
                "input_count": before,
                "output_count": len(current),
                "removed": removed_conf,
            })
        else:
            stages.append({
                "name": "confidence_gate",
                "input_count": len(current),
                "output_count": len(current),
                "removed": 0,
                "skipped": True,
            })

        # Stage 2: Relevance threshold
        before = len(current)
        current, removed_thr = self._apply_relevance_threshold(current)
        stages.append({
            "name": "relevance_threshold",
            "input_count": before,
            "output_count": len(current),
            "removed": removed_thr,
        })

        # Stage 3: Diversity dedup
        before = len(current)
        current, removed_div = self._deduplicate_by_diversity(current)
        stages.append({
            "name": "diversity_dedup",
            "input_count": before,
            "output_count": len(current),
            "removed": removed_div,
        })

        # Stage 4: Sort
        before = len(current)
        current = self._sort_by_recency_and_relevance(current)
        stages.append({
            "name": "sort",
            "input_count": before,
            "output_count": len(current),
            "removed": 0,
        })

        # Stage 5: Token budget
        before = len(current)
        current, token_count, exceeded = self._apply_token_budget(current)
        stages.append({
            "name": "token_budget",
            "input_count": before,
            "output_count": len(current),
            "removed": before - len(current),
            "tokens": token_count,
            "max_allowed": self.max_tokens,
            "budget_exceeded": exceeded,
        })

        total_tokens = token_count
        total_removed = total - len(current)

        return InjectorResult(
            refined_memories=current,
            total_candidates=total,
            total_removed=total_removed,
            total_tokens=total_tokens,
            max_allowed=self.max_tokens,
            diversity_removed=removed_div,
            threshold_removed=removed_thr,
            budget_exceeded=exceeded,
            metadata={"stages": stages},
        )

    # ── stage implementations ──────────────────────────────────────────

    def _apply_relevance_threshold(self, memories: List[Dict]) -> tuple:
        """Drop memories whose search score is below relevance_threshold."""
        kept: List[Dict] = []
        removed = 0
        for m in memories:
            score = m.get("score")
            if score is None:
                # No score → keep (conservative)
                kept.append(m)
            elif isinstance(score, (int, float)) and score >= self.relevance_threshold:
                kept.append(m)
            else:
                removed += 1
        return kept, removed

    def _deduplicate_by_diversity(self, memories: List[Dict]) -> tuple:
        """Greedy dedup: keep high-score first, drop near-duplicates."""
        if len(memories) <= 1:
            return list(memories), 0

        # Sort by score descending (stable dedup order)
        sorted_mems = sorted(
            memories,
            key=lambda m: m.get("score", 0.0) or 0.0,
            reverse=True,
        )
        kept: List[Dict] = []
        removed = 0
        for m in sorted_mems:
            content = m.get("content") or ""
            is_dup = False
            for kept_m in kept:
                kept_content = kept_m.get("content") or ""
                sim = _jaccard_similarity(content, kept_content)
                if sim >= self.diversity_threshold:
                    is_dup = True
                    break
            if is_dup:
                removed += 1
            else:
                kept.append(m)
        return kept, removed

    def _sort_by_recency_and_relevance(self, memories: List[Dict]) -> List[Dict]:
        """Composite sort: recency * w_recency + relevance * w_relevance.

        recency_score: normalized (now - created_at) → 1.0 (recent) to 0.0 (old).
        relevance_score: memory["score"] or 0.0.
        """
        now = time.time()

        def _composite(m: Dict) -> float:
            # Recency
            created_at = m.get("created_at") or m.get("timestamp")
            recency = 0.0
            if created_at:
                try:
                    import re as _re
                    from datetime import datetime as _dt
                    ts_str = _re.sub(r'[Zz\+].*$', '', str(created_at))
                    dt_val = _dt.fromisoformat(ts_str)
                    age_hours = max(0.0, (now - dt_val.timestamp()) / 3600.0)
                    # Half-life 168 hours (1 week) → score = 1 / (1 + age/168)
                    recency = 1.0 / (1.0 + age_hours / 168.0)
                except (ValueError, TypeError, OSError):
                    recency = 0.0

            # Relevance
            relevance = m.get("score", 0.0) or 0.0
            if isinstance(relevance, (int, float)):
                relevance = float(relevance)
            else:
                relevance = 0.0

            return recency * self.recency_weight + relevance * self.relevance_weight

        return sorted(memories, key=_composite, reverse=True)

    def _apply_token_budget(self, memories: List[Dict]) -> tuple:
        """Truncate to fit within max_tokens.

        Returns: (truncated_list, total_tokens, budget_exceeded).
        """
        kept: List[Dict] = []
        total = 0
        exceeded = False
        for m in memories:
            content = m.get("content") or ""
            mem_tokens = estimate_tokens(content)
            if total + mem_tokens > self.max_tokens:
                exceeded = True
                # Try to include if it fits alone (never drop all)
                if not kept:
                    kept.append(m)
                    total = mem_tokens
                break
            kept.append(m)
            total += mem_tokens
        return kept, total, exceeded
