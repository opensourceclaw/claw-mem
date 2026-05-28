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
Dreaming Engine (v4.12.0)

Four-phase pipeline that transforms short-term episodic memories into
long-term semantic/procedural knowledge and reusable skills.

Architecture:
    light → deep → REM → promote
      ↓       ↓      ↓       ↓
    ingest  score  extract  write

Public API:
    DreamingConfig      — Weight configuration and thresholds.
    DreamingPipeline    — Full pipeline orchestrator.
    DreamingResult      — Pipeline run result.
    SignalIngestor      — Light-phase signal ingestion.
    CandidateScorer     — Deep-phase six-dimension scoring.
    ScoredCandidate     — Scored signal with dimension scores.
    PatternExtractor    — REM-phase pattern extraction.
    REMResult           — Extraction result.
    Promoter            — Promote-phase persistence engine.
    PromotionResult     — Promotion statistics.
    Signal              — Staged memory signal.
"""

from .config import DreamingConfig
from .deep import CandidateScorer, ScoredCandidate
from .light import Signal, SignalIngestor
from .pipeline import DreamingPipeline, DreamingResult
from .promote import Promoter, PromotionResult
from .rem import PatternExtractor, REMResult

__all__ = [
    "DreamingConfig",
    "DreamingPipeline",
    "DreamingResult",
    "SignalIngestor",
    "CandidateScorer",
    "ScoredCandidate",
    "PatternExtractor",
    "REMResult",
    "Promoter",
    "PromotionResult",
    "Signal",
]
