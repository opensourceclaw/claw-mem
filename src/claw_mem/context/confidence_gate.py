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

"""F2: ConfidenceGate + GateResult + ConfidenceLevel (v4.9.0 context control plane).

Four-dimensional confidence scoring:
  1. Vector  – search-result score as proxy for embedding distance
  2. Time    – TieredDecayEngine.classify() → tier-based decay signal
  3. Conflict– ConflictDetector batch cache; memory in any conflict scores low
  4. Frequency– tag-driven heuristic (e.g. missing tags → lower confidence)

When a dimension is unavailable (e.g. no TieredDecayEngine enabled), its weight
is redistributed proportionally across the remaining dimensions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class GateResult:
    """Individual evaluation result for a single memory."""

    memory_id: Optional[str]
    confidence_score: float
    confidence_level: ConfidenceLevel
    vector_score: float
    time_score: float
    conflict_score: float
    frequency_score: float
    reason: str = ""
    warning: Optional[str] = None


class ConfidenceGate:
    """Filters memories by four-dimensional confidence before context injection.

    Keeps HIGH (>= high_threshold) and MEDIUM memories; discards LOW
    (< low_threshold).  When a component is unavailable its weight is
    proportionally redistributed to the other dimensions.
    """

    # v4.9.0 defaults
    DEFAULT_HIGH = 0.7
    DEFAULT_LOW = 0.4
    DEFAULT_W_VECTOR = 0.4
    DEFAULT_W_TIME = 0.3
    DEFAULT_W_CONFLICT = 0.2
    DEFAULT_W_FREQUENCY = 0.1

    def __init__(
        self,
        manager: Any = None,
        high_threshold: float = DEFAULT_HIGH,
        low_threshold: float = DEFAULT_LOW,
        weight_vector: float = DEFAULT_W_VECTOR,
        weight_time: float = DEFAULT_W_TIME,
        weight_conflict: float = DEFAULT_W_CONFLICT,
        weight_frequency: float = DEFAULT_W_FREQUENCY,
    ):
        self.manager = manager
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.weight_vector = weight_vector
        self.weight_time = weight_time
        self.weight_conflict = weight_conflict
        self.weight_frequency = weight_frequency

        # Cached conflict-id set (populated once per filter batch)
        self._conflict_cache: Optional[Set[str]] = None
        self._conflict_cache_filled = False

    # ── public API ─────────────────────────────────────────────────────

    def evaluate(self, memory: Dict[str, Any]) -> GateResult:
        """Score a single memory across four dimensions."""
        return self._score(memory)

    def evaluate_batch(self, memories: List[Dict]) -> List[GateResult]:
        """Score a batch of memories (builds conflict cache once)."""
        self._fill_conflict_cache()
        results = [self._score(m) for m in memories]
        self._reset_conflict_cache()
        return results

    def filter(self, memories: List[Dict]) -> List[Dict]:
        """Main entry point: evaluate batch then drop LOW-confidence items."""
        results = self.evaluate_batch(memories)
        kept: List[Dict] = []
        for i, result in enumerate(results):
            if result.confidence_level != ConfidenceLevel.LOW:
                kept.append(memories[i])
        return kept

    # ── scoring ────────────────────────────────────────────────────────

    def _score(self, memory: Dict[str, Any]) -> GateResult:
        """Composite score with weight redistribution on unavailable dims."""
        mem_id = memory.get("id")

        vs = self._compute_vector_score(memory)
        ts = self._compute_time_score(memory)
        cs = self._compute_conflict_score(memory)
        fs = self._compute_frequency_score(memory)

        # Determine which dimensions are available
        available = {
            "vector": vs is not None,
            "time": ts is not None,
            "conflict": cs is not None,
            "frequency": fs is not None,
        }
        # Gather effective weights, redistributing if unavailable
        eff_w = self._effective_weights(available)

        vs_val = vs if vs is not None else 0.0
        ts_val = ts if ts is not None else 0.0
        cs_val = cs if cs is not None else 0.0
        fs_val = fs if fs is not None else 0.0

        composite = (
            vs_val * eff_w["vector"]
            + ts_val * eff_w["time"]
            + cs_val * eff_w["conflict"]
            + fs_val * eff_w["frequency"]
        )

        # Map composite → level
        if composite >= self.high_threshold:
            level = ConfidenceLevel.HIGH
        elif composite >= self.low_threshold:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        warnings = []
        if not available["time"]:
            warnings.append("time_score_unavailable")
        if not available["conflict"]:
            warnings.append("conflict_score_unavailable")

        reason = (
            f"vec={vs_val:.2f} t={ts_val:.2f} c={cs_val:.2f} f={fs_val:.2f}"
            f" → {composite:.2f} ({level.value})"
        )

        return GateResult(
            memory_id=mem_id,
            confidence_score=round(composite, 4),
            confidence_level=level,
            vector_score=round(vs_val, 4),
            time_score=round(ts_val, 4),
            conflict_score=round(cs_val, 4),
            frequency_score=round(fs_val, 4),
            reason=reason,
            warning="; ".join(warnings) if warnings else None,
        )

    def _effective_weights(self, available: Dict[str, bool]) -> Dict[str, float]:
        """If a dimension is unavailable, redistribute its weight proportionally."""
        w = {
            "vector": self.weight_vector,
            "time": self.weight_time,
            "conflict": self.weight_conflict,
            "frequency": self.weight_frequency,
        }
        unavailable_weight = sum(
            w[dim] for dim, ok in available.items() if not ok
        )
        available_weight = sum(
            w[dim] for dim, ok in available.items() if ok
        )
        if unavailable_weight <= 0 or available_weight <= 0:
            return w

        redistributed = unavailable_weight / available_weight
        for dim in w:
            if available[dim]:
                w[dim] += w[dim] * redistributed
            else:
                w[dim] = 0.0
        return w

    # ── dimension helpers ──────────────────────────────────────────────

    def _compute_vector_score(self, memory: Dict) -> Optional[float]:
        """Use search result `score` field as proxy for embedding distance.

        Returns None when the dimension should be treated as unavailable.
        """
        score = memory.get("score")
        if score is None:
            return None
        try:
            return float(score)
        except (TypeError, ValueError):
            return None

    def _compute_time_score(self, memory: Dict) -> Optional[float]:
        """Map TieredDecayEngine.classify() tier → numeric score.

        HOT=1.0, WARM=0.6, COLD=0.3.  Returns None if tiered decay is not
        enabled / available.
        """
        if self.manager is None:
            return None
        td = getattr(self.manager, "tiered_decay", None)
        if td is None:
            return None
        from ..decay.tiered_decay import TierLevel

        tier = td.classify(memory)
        return {TierLevel.HOT: 1.0, TierLevel.WARM: 0.6, TierLevel.COLD: 0.3}.get(
            tier, 0.3
        )

    def _compute_conflict_score(self, memory: Dict) -> Optional[float]:
        """Batch-conflict lookup: 0.3 if ID in any conflict, 1.0 if clean.

        Returns None when ConflictDetector is not available.
        """
        if self.manager is None:
            return None
        cd = getattr(self.manager, "conflict_detector", None)
        if cd is None:
            return None

        mem_id = memory.get("id")
        if mem_id is None:
            return 0.5  # unknown identity → neutral

        if self._conflict_cache is not None:
            return 0.3 if mem_id in self._conflict_cache else 1.0
        return 1.0  # no cache → assume clean (conservative)

    def _compute_frequency_score(self, memory: Dict) -> float:
        """Tag-driven heuristic: missing tags=0.5, has tags=0.8, critical=1.0."""
        tags = memory.get("tags") or memory.get("metadata", {}).get("tags") or []
        if not tags:
            return 0.5
        critical_keywords = ("critical", "important", "永久", "关键", "critical_rule")
        for t in tags:
            if isinstance(t, str) and any(kw in t.lower() for kw in critical_keywords):
                return 1.0
        return 0.8

    # ── conflict cache ─────────────────────────────────────────────────

    def _fill_conflict_cache(self) -> None:
        """Run ConflictDetector.detect_conflicts() once and cache conflicted IDs."""
        if self._conflict_cache_filled:
            return
        if self.manager is None:
            self._conflict_cache_filled = True
            return
        cd = getattr(self.manager, "conflict_detector", None)
        if cd is None:
            self._conflict_cache_filled = True
            return
        try:
            conflicts = cd.detect_conflicts()
            ids: Set[str] = set()
            for c in conflicts:
                ids.add(c.memory_id_a)
                ids.add(c.memory_id_b)
            self._conflict_cache = ids
        except Exception:
            self._conflict_cache = set()
        self._conflict_cache_filled = True

    def _reset_conflict_cache(self) -> None:
        self._conflict_cache = None
        self._conflict_cache_filled = False
