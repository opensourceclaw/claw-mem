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
Dreaming Engine — Pipeline (v4.12.0)

Orchestrates the complete light→deep→REM→promote pipeline.
Supports dry_run mode (score-only, no persistence).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import DreamingConfig
    from .rem import REMResult
    from .promote import PromotionResult


@dataclass
class DreamingResult:
    """Full result of a dreaming pipeline run.

    Attributes:
        staged: Number of signals staged in light phase.
        scored: Number of candidates scored in deep phase.
        passed: Number of candidates passing the filter.
        promoted: Total promotions (episodic + semantic + procedural).
        skills_stored: Number of skills persisted.
        duration_ms: Pipeline wall-clock duration in milliseconds.
        dry_run: Whether this was a dry run.
        error: Error message if the pipeline failed (None on success).
        promotion_detail: Detailed PromotionResult (None on dry_run).
    """

    staged: int = 0
    scored: int = 0
    passed: int = 0
    promoted: int = 0
    skills_stored: int = 0
    duration_ms: float = 0.0
    dry_run: bool = False
    error: Optional[str] = None
    promotion_detail: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "staged": self.staged,
            "scored": self.scored,
            "passed": self.passed,
            "promoted": self.promoted,
            "skills_stored": self.skills_stored,
            "duration_ms": round(self.duration_ms, 2),
            "dry_run": self.dry_run,
        }
        if self.error:
            d["error"] = self.error
        if self.promotion_detail:
            d["promotion_detail"] = self.promotion_detail
        return d


class DreamingPipeline:
    """Full dreaming pipeline: light → deep → REM → promote.

    Usage::

        from claw_mem import MemoryManager
        from claw_mem.dreaming import DreamingPipeline, DreamingConfig

        mm = MemoryManager()
        config = DreamingConfig(dry_run=True)
        pipeline = DreamingPipeline(mm, config=config)
        result = pipeline.run()
    """

    def __init__(
        self,
        memory_manager: Any,
        config: Optional[DreamingConfig] = None,
        llm_provider: Any = None,
    ):
        from .config import DreamingConfig

        self._mm = memory_manager
        self._config = config or DreamingConfig()
        self._llm = llm_provider

        # Last run stats
        self._last_result: Optional[DreamingResult] = None

    # ── public API ─────────────────────────────────────────────────

    def run(self) -> DreamingResult:
        """Execute the full dreaming pipeline.

        Returns:
            DreamingResult with stage counts and timing.
        """
        t0 = time.time()
        result = DreamingResult(dry_run=self._config.dry_run)

        try:
            # ── Phase 1: Light (ingest signals) ────
            from .light import SignalIngestor

            ingestor = SignalIngestor(self._mm, config=self._config)
            staged_count = ingestor.ingest()
            result.staged = staged_count

            if staged_count == 0:
                result.duration_ms = (time.time() - t0) * 1000
                self._last_result = result
                return result

            signals = ingestor._staged

            # ── Phase 2: Deep (score candidates) ────
            from .deep import CandidateScorer

            scorer = CandidateScorer(config=self._config)
            all_candidates = scorer.score_all(signals)
            result.scored = len(all_candidates)

            passed = scorer.filter(all_candidates)
            result.passed = len(passed)

            if len(passed) == 0:
                result.duration_ms = (time.time() - t0) * 1000
                self._last_result = result
                return result

            # ── Phase 3: REM (extract patterns) ────
            from .rem import PatternExtractor

            extractor = PatternExtractor(llm_provider=self._llm)
            rem_result = extractor.extract(passed)

            # ── Phase 4: Promote (persist) ────
            from .promote import Promoter

            promoter = Promoter(self._mm, dry_run=self._config.dry_run)
            promotion = promoter.promote(passed, rem_result)
            result.promoted = promotion.total
            result.skills_stored = promotion.skill_stored
            result.promotion_detail = promotion.to_dict()

            # ── Store skills from REM ────
            if rem_result.skills and not self._config.dry_run:
                result.skills_stored = promotion.skill_stored

        except Exception as e:
            result.error = str(e)

        result.duration_ms = (time.time() - t0) * 1000
        self._last_result = result
        return result

    def last_result(self) -> Optional[DreamingResult]:
        """Get the result of the last pipeline run."""
        return self._last_result
