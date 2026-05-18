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
claw-mem Core Memory Manager

Coordinates three-layer memory architecture (Working/Short-term/Long-term) and three memory types (Episodic/Semantic/Procedural).
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .storage.episodic import EpisodicStorage
from .storage.semantic import SemanticStorage
from .storage.procedural import ProceduralStorage
from .storage.index import InMemoryIndex, WorkingMemoryCache
from .retrieval.keyword import KeywordRetriever
from .retrieval.bm25_retriever import BM25Retriever, HybridBM25Retriever
from .retrieval.entity_retriever import EntityEnhancedRetriever, HybridEntityRetriever
from .retrieval.heuristic_retriever import HeuristicRetriever, SmartRetriever, HeuristicConfig
from .retrieval.enhanced_smart_retriever import EnhancedSmartRetriever
from .retrieval.three_tier import ThreeTierRetriever, SessionStartupHook
from .retrieval.query_cache import QueryCache, get_query_cache
from .retrieval.synonym_expander import SynonymExpander, get_synonym_expander
from .retrieval.search_stats import SearchStats, get_search_stats
from .security.validation import WriteValidator
from .security.checkpoint import CheckpointManager
from .security.audit import AuditLogger
from .config import ConfigDetector
from .importance import ImportanceScorer
from .memory_fix_plugin import MemoryFixPlugin
from .memory_decay import MemoryDecay
from .rule_extractor import RuleExtractor
from .gating import WriteTimeGating
from .reflection import ReflectionOrchestrator, ReflectionResult
from .temporal import TimeWeightCalculator, TimeWeightConfig
from .compression.memory_compression_v2 import MemoryCompressorV2, CompressionConfig, CompressionResult
# v2.14.0: Graph + Decay + GroundTruth
from .graph.multi_graph import MultiGraphMemory
from .graph.dual_layer import DualLayerMemory
from .decay import DecayController, DecayScheduler, DecayConfig
from .storage.ground_truth import GroundTruthStore
# v2.15.0: Engram + Spreading + Compression
from .retrieval.engram import EngramIndex
from .retrieval.spreading import SpreadingActivation
from .retrieval.decoupled import DecoupledRetriever
from .compression.spectrum import CompressionSpectrum
# v2.19.0: Cache + Monitor
from .cache.query_cache import QueryCache
from .monitor.performance import PerformanceMonitor
# v2.20.0: Error types
from .errors import (
    ClawMemError, StorageError, RetrievalError,
    MemoryNotFoundError, IndexNotReadyError, QueryTooLongError,
)
# v3.0.0-rc.1: CMS Perception Layer
from .cms import (
    CapacityMonitor, ContextWarningHook, ImportanceEvaluator,
    SessionSummaryGenerator, MemoryDeduplicator,
    CompressionStrategySelector,
    SessionStateMachine, ContextSwitcher, RecoveryMechanism, SnapshotStorage,
)
from .cms.compression_result import CompressionResult
import time


def _log(message: str):
    """Print message unless in silent mode (checks env at runtime)"""
    if not os.environ.get('CLAW_MEM_SILENT'):
        print(message)


class MemoryManager:
    """
    Memory Manager
    
    Core responsibilities:
    1. Manage three-layer memory architecture
    2. Provide storage and retrieval interfaces
    3. Auto-save and load
    4. Security validation and auditing
    """
    
    def __init__(self, workspace: Optional[str] = None, auto_detect: bool = True,
                 enable_gating: bool = False, gating_threshold: float = 0.6,
                 enable_graph: bool = False,
                 bm25_k1: float = 1.5, bm25_b: float = 0.75,
                 bm25_weight: float = 0.7, keyword_weight: float = 0.3,
                 recency_boost: float = 1.0, frequency_boost: float = 1.0,
                 enable_cache: bool = True, enable_synonyms: bool = True,
                 enable_stats: bool = True, enable_compression: bool = True,
                 # v2.14.0: Decay + GroundTruth
                 enable_decay: bool = True,
                 enable_ground_truth: bool = True,
                 decay_config: "DecayConfig" = None,
                 # v2.15.0: Engram + Spreading + Compression
                 enable_engram: bool = True,
                 enable_spreading: bool = True,
                 enable_compression_spectrum: bool = True,
                 # v2.18.0: CompressionSpectrum thresholds
                 compression_trigger_access: int = 5,
                 compression_trigger_apply: int = 3,
                 compression_trigger_verify: int = 2,
                 engram_ngram_size: int = 3,
                 spreading_max_depth: int = 2,
                 spreading_decay_factor: float = 0.5,
                 spreading_threshold: float = 0.1,
                 # v3.0.0-rc.1: CMS Perception Layer
                 enable_cms: bool = False,
                 cms_token_threshold: int = 8000,
                 cms_memory_threshold: int = 1000,
                 cms_warning_level: float = 0.8):
        """
        Initialize Memory Manager

        Args:
            workspace: OpenClaw workspace path (optional, auto-detect if None)
            auto_detect: Enable auto-detection (default: True)
            enable_gating: Enable Write-Time Gating (default: False)
            gating_threshold: Salience threshold for gating (default: 0.6)
            enable_graph: Enable Concept-Mediated Graph (default: False)
            bm25_k1: BM25 k1 parameter (default 1.5)
            bm25_b: BM25 b parameter (default 0.75)
            bm25_weight: BM25 weight in hybrid search (default 0.7)
            keyword_weight: Keyword weight in hybrid search (default 0.3)
            recency_boost: Recency boost multiplier (default 1.0 = off)
            frequency_boost: Frequency boost multiplier (default 1.0 = off)
            enable_cache: Enable query result cache (default: True)
            enable_synonyms: Enable synonym expansion (default: True)
            enable_stats: Enable search statistics tracking (default: True)
        """
        # Auto-detect workspace if not provided
        if workspace is None and auto_detect:
            workspace = ConfigDetector.detect_workspace()
        elif workspace is None:
            # Fallback to default if auto-detect disabled
            workspace = "~/.openclaw/workspace"
        
        self.workspace = Path(workspace).expanduser()
        self.session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None

        # Store BM25 config for lazy initialization
        self._bm25_k1 = bm25_k1; self._bm25_b = bm25_b
        self._bm25_weight = bm25_weight; self._keyword_weight = keyword_weight
        self._recency_boost = recency_boost; self._frequency_boost = frequency_boost

        # Lightweight working state (kept eager)
        self.working_cache = WorkingMemoryCache(max_size=100, ttl_seconds=300)
        self.working_memory: List[Dict] = []
        self.index = InMemoryIndex(ngram_size=3, enable_persistence=True)

        # Lazy-initialized caches
        self._episodic = None; self._semantic = None; self._procedural = None
        self._retriever = None; self._bm25_retriever = None; self._hybrid_retriever = None
        self._entity_retriever = None; self._hybrid_entity_retriever = None
        self._heuristic_retriever = None; self._smart_retriever = None
        self._enhanced_smart_retriever = None; self._three_tier_retriever = None
        self._session_startup_hook = None
        self._validator = None; self._checkpoint = None; self._audit = None
        self._importance_scorer = None
        self._memory_fix = None; self._memory_decay = None; self._rule_extractor = None

        # Write-Time Gating (lazy init)
        self.enable_gating = enable_gating
        self.gating_threshold = gating_threshold
        self._gating = None

        # Concept-Mediated Graph (lazy init)
        self.enable_graph = enable_graph
        self._graph = None

        # v2.14.0: MultiGraph + DualLayer + Decay + GroundTruth
        self.enable_decay = enable_decay
        self.enable_ground_truth = enable_ground_truth
        self._decay_config = decay_config or DecayConfig.default()
        self._multi_graph: Optional[MultiGraphMemory] = None
        self._dual_layer: Optional[DualLayerMemory] = None
        self._decay_controller: Optional[DecayController] = None
        self._decay_scheduler: Optional[DecayScheduler] = None
        self._ground_truth: Optional[GroundTruthStore] = None

        # v2.15.0: Engram + Spreading + Compression
        self.enable_engram = enable_engram
        self.enable_spreading = enable_spreading
        self.enable_compression = enable_compression
        self._engram_ngram_size = engram_ngram_size
        self._spreading_max_depth = spreading_max_depth
        self._spreading_decay_factor = spreading_decay_factor
        self._spreading_threshold = spreading_threshold
        self._engram: Optional[EngramIndex] = None
        self._spreader: Optional[SpreadingActivation] = None
        self._decoupled_retriever: Optional[DecoupledRetriever] = None
        self._compression_spectrum: Optional[CompressionSpectrum] = None
        self.enable_compression_spectrum = enable_compression_spectrum
        self._compression_trigger_access = compression_trigger_access
        self._compression_trigger_apply = compression_trigger_apply
        self._compression_trigger_verify = compression_trigger_verify

        # v2.19.0: Cache + Monitor
        self.enable_query_cache = True
        self._cache_max_size = 1000
        self._query_cache: Optional[QueryCache] = None
        self._performance_monitor: Optional[PerformanceMonitor] = None

        # v3.0.0-rc.1: CMS Perception Layer
        self.enable_cms = enable_cms
        self._cms_token_threshold = cms_token_threshold
        self._cms_memory_threshold = cms_memory_threshold
        self._cms_warning_level = cms_warning_level
        self._cms_capacity: Optional[CapacityMonitor] = None
        self._cms_hook: Optional[ContextWarningHook] = None
        self._cms_importance: Optional[ImportanceEvaluator] = None
        # v3.0.0-rc.2: Compression layer
        self._cms_summarizer: Optional[SessionSummaryGenerator] = None
        self._cms_deduplicator: Optional[MemoryDeduplicator] = None
        self._cms_strategy: Optional[CompressionStrategySelector] = None

        # Search mode
        self.search_mode = os.environ.get('CLAW_MEM_SEARCH_MODE', 'enhanced_smart')

        # v2.9.0: Cache, Synonyms, Statistics
        self.enable_cache = enable_cache
        self.enable_synonyms = enable_synonyms
        self.enable_stats = enable_stats
        self._query_cache = None
        self._synonym_expander = None
        self._search_stats = None
        self._reflection = None  # v2.9.1
        self._time_weight = None  # v2.9.1
        self.enable_compression = enable_compression
        self._compressor: Optional[MemoryCompressorV2] = None  # v2.12.0
        self._compression_config = CompressionConfig()  # v2.12.0

        # v2.13.0: Critical rules — never compressed, always injected
        self._critical_rules: Dict[str, dict] = {}
        self._critical_rules_file = os.path.join(
            os.path.expanduser("~/.claw-mem"), "critical_rules.json"
        )
        self._load_critical_rules()

    # ── v2.20.0: State validation ─────────────────────────────────

    def _validate_state(self) -> None:
        """Validate MemoryManager state before operations."""
        if not self.workspace or not self.workspace.exists():
            raise StorageError("Workspace does not exist")
        if self.index is None:
            raise IndexNotReadyError("Memory index not initialized")

    # ── v2.20.0: Error handling ───────────────────────────────────

    def _handle_error(self, error: Exception, operation: str,
                      fallback=None):
        """Centralized error handling with graceful degradation."""
        import logging
        logger = logging.getLogger("claw_mem")
        logger.warning(f"{operation} failed: {error}", exc_info=False)
        if fallback is not None:
            return fallback
        raise

    def _validate_session_memory(self):
        """Validate memory at session start (F000 fix)"""
        validation = self.memory_fix.validate_session_memory()
        
        if not validation['valid']:
            # Log error but do not block startup
            self.audit.log("MEMORY_VALIDATION_FAILED", str(validation['errors']))
        
        if validation['warnings']:
            # Log warning
            for warning in validation['warnings']:
                self.audit.log("MEMORY_WARNING", warning)
        
        # L1: Working Memory (In-Memory Index + Cache)
        # Enable index persistence for fast startup
        self.index = InMemoryIndex(ngram_size=3, enable_persistence=True)
        self.working_cache = WorkingMemoryCache(max_size=100, ttl_seconds=300)
        self.working_memory: List[Dict] = []
        
        # Only print if not in silent mode (e.g., when used as a bridge)
        if not os.environ.get('CLAW_MEM_SILENT'):
            _log(f"🧠 claw-mem initialized, workspace: {self.workspace}")

    # ── Lazy properties for deferred initialization ──

    @property
    def episodic(self):
        if self._episodic is None:
            self._episodic = EpisodicStorage(self.workspace)
        return self._episodic

    @property
    def semantic(self):
        if self._semantic is None:
            self._semantic = SemanticStorage(self.workspace)
        return self._semantic

    @property
    def procedural(self):
        if self._procedural is None:
            self._procedural = ProceduralStorage(self.workspace)
        return self._procedural

    @property
    def bm25_retriever(self):
        if self._bm25_retriever is None:
            self._bm25_retriever = BM25Retriever(
                k1=self._bm25_k1, b=self._bm25_b,
                recency_boost=self._recency_boost, frequency_boost=self._frequency_boost)
        return self._bm25_retriever

    @property
    def hybrid_retriever(self):
        if self._hybrid_retriever is None:
            self._hybrid_retriever = HybridBM25Retriever(
                k1=self._bm25_k1, b=self._bm25_b,
                bm25_weight=self._bm25_weight, keyword_weight=self._keyword_weight,
                recency_boost=self._recency_boost, frequency_boost=self._frequency_boost)
        return self._hybrid_retriever

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = KeywordRetriever()
        return self._retriever

    @property
    def entity_retriever(self):
        if self._entity_retriever is None:
            self._entity_retriever = EntityEnhancedRetriever(use_spacy=False)
        return self._entity_retriever

    @property
    def hybrid_entity_retriever(self):
        if self._hybrid_entity_retriever is None:
            self._hybrid_entity_retriever = HybridEntityRetriever(use_spacy=False)
        return self._hybrid_entity_retriever

    @property
    def heuristic_retriever(self):
        if self._heuristic_retriever is None:
            self._heuristic_retriever = HeuristicRetriever()
        return self._heuristic_retriever

    @property
    def smart_retriever(self):
        if self._smart_retriever is None:
            self._smart_retriever = SmartRetriever()
        return self._smart_retriever

    @property
    def enhanced_smart_retriever(self):
        if self._enhanced_smart_retriever is None:
            self._enhanced_smart_retriever = EnhancedSmartRetriever()
        return self._enhanced_smart_retriever

    @property
    def three_tier_retriever(self):
        if self._three_tier_retriever is None:
            self._three_tier_retriever = ThreeTierRetriever(self.workspace)
        return self._three_tier_retriever

    @property
    def session_startup_hook(self):
        if self._session_startup_hook is None:
            self._session_startup_hook = SessionStartupHook(self.three_tier_retriever)
        return self._session_startup_hook

    @property
    def validator(self):
        if self._validator is None:
            self._validator = WriteValidator()
        return self._validator

    @property
    def checkpoint(self):
        if self._checkpoint is None:
            self._checkpoint = CheckpointManager(self.workspace)
        return self._checkpoint

    @property
    def audit(self):
        if self._audit is None:
            self._audit = AuditLogger(self.workspace)
        return self._audit

    @property
    def importance_scorer(self):
        if self._importance_scorer is None:
            self._importance_scorer = ImportanceScorer()
        return self._importance_scorer

    @property
    def memory_fix(self):
        if self._memory_fix is None:
            self._memory_fix = MemoryFixPlugin(self.workspace)
        return self._memory_fix

    @property
    def memory_decay(self):
        if self._memory_decay is None:
            self._memory_decay = MemoryDecay(self.workspace)
        return self._memory_decay

    @property
    def rule_extractor(self):
        if self._rule_extractor is None:
            self._rule_extractor = RuleExtractor(self.workspace)
        return self._rule_extractor

    @property
    def gating(self):
        if self._gating is None and self.enable_gating:
            self._gating = WriteTimeGating(threshold=self.gating_threshold)
        return self._gating

    @property
    def graph(self):
        if self._graph is None and self.enable_graph:
            from claw_mem.graph import ConceptMediatedGraph, DummyEmbedder, KeywordExtractor
            self._graph = ConceptMediatedGraph(
                embedder=DummyEmbedder(), extractor=KeywordExtractor())
        return self._graph

    @property
    def query_cache(self) -> Optional[QueryCache]:
        """v2.9.0: Query result cache for fast repeated searches."""
        if self._query_cache is None and self.enable_cache:
            self._query_cache = get_query_cache()
        return self._query_cache

    @property
    def synonym_expander(self) -> Optional[SynonymExpander]:
        """v2.9.0: Synonym expander for improved recall."""
        if self._synonym_expander is None and self.enable_synonyms:
            self._synonym_expander = get_synonym_expander()
        return self._synonym_expander

    @property
    def search_stats(self) -> Optional[SearchStats]:
        """v2.9.0: Search statistics tracker."""
        if self._search_stats is None and self.enable_stats:
            self._search_stats = get_search_stats()
        return self._search_stats

    @property
    def reflection(self) -> Optional[ReflectionOrchestrator]:
        """v2.9.1: Reflection orchestrator."""
        if self._reflection is None:
            self._reflection = ReflectionOrchestrator()
        return self._reflection

    @property
    def time_weight_calc(self) -> Optional[TimeWeightCalculator]:
        """v2.9.1: Time-aware weight calculator."""
        if self._time_weight is None:
            self._time_weight = TimeWeightCalculator()
        return self._time_weight

    def get_search_statistics(self) -> Optional[Dict]:
        """Get search performance statistics (v2.9.0).

        Returns latency percentiles, cache hit rate, and accuracy metrics.
        """
        if self.search_stats:
            return self.search_stats.get_stats()
        return None

    def batch_search(self, queries: List[str], memory_type: Optional[str] = None,
                     metadata: Optional[Dict] = None, limit: int = 10,
                     mode: Optional[str] = None) -> List[List[Dict]]:
        """Batch search multiple queries efficiently (v2.9.0 P2-1).

        Args:
            queries: List of search queries
            memory_type: Memory type filter (optional)
            metadata: Optional metadata filter
            limit: Number of results per query
            mode: Search mode

        Returns:
            List of result lists (one per query)
        """
        return [self.search(q, memory_type=memory_type,
                           metadata=metadata, limit=limit, mode=mode)
                for q in queries]

    def reflect(self, user_id: str = "", force: bool = False) -> ReflectionResult:
        """Execute a reflection cycle (v2.9.1).

        Collects recent memories, extracts observations, synthesizes beliefs,
        and tracks changes over time.

        Args:
            user_id: User identifier for belief attribution
            force: Force reflection even if few observations

        Returns:
            ReflectionResult with observations, beliefs, and summary
        """
        # Collect recent memories for reflection
        recent = self.episodic.get_recent(50)
        recent.extend(self.semantic.get_all())

        return self.reflection.reflect(recent, user_id=user_id, force=force)

    def get_beliefs(self, user_id: str = "",
                   include_history: bool = False) -> List[Dict]:
        """Get current beliefs and optionally their version history (v2.9.1).

        Args:
            user_id: User identifier (unused for now)
            include_history: Include version history for each belief

        Returns:
            List of belief dicts
        """
        return self.reflection.get_beliefs(include_history=include_history)

    def get_reflection_stats(self) -> Dict:
        """Get reflection statistics (v2.9.1)."""
        return self.reflection.get_reflection_stats()

    @property
    def compressor(self) -> MemoryCompressorV2:
        """v2.12.0: Memory compressor for automatic memory consolidation."""
        if self._compressor is None:
            self._compressor = MemoryCompressorV2(self._compression_config)
        return self._compressor

    def compress(self, force: bool = False) -> Optional[CompressionResult]:
        """Compress memories to reduce storage (v2.12.0).

        Triggers when memory count exceeds threshold or at forced intervals.
        Uses similarity-based deduplication and Knowledge Block extraction.

        Args:
            force: Force compression regardless of thresholds

        Returns:
            CompressionResult if compression was executed, None otherwise
        """
        if not self.enable_compression:
            return None

        all_memories = (list(self.episodic.get_recent(200)) +
                       list(self.semantic.get_all()) +
                       list(self.procedural.get_all()))

        if not force and len(all_memories) < self._compression_config.max_memories:
            return None

        return self.compressor.compress(all_memories)

    def get_compression_config(self) -> Dict:
        """Get current compression configuration (v2.12.0)."""
        return self._compression_config.to_dict()

    def get_compression_history(self) -> Dict:
        """Get compression statistics (v2.12.0)."""
        return {
            "compression_count": self.compressor.compression_count,
            "operation_count": self.compressor.operation_count,
            "last_compression_idx": self.compressor.last_compression_idx,
        }

    # ========================================================================
    # Critical Rules (v2.13.0)
    # ========================================================================

    def _load_critical_rules(self) -> None:
        """Load critical rules from disk."""
        try:
            if os.path.exists(self._critical_rules_file):
                with open(self._critical_rules_file, 'r', encoding='utf-8') as f:
                    self._critical_rules = json.load(f)
        except Exception:
            self._critical_rules = {}

    def _save_critical_rules(self) -> None:
        """Persist critical rules to disk."""
        os.makedirs(os.path.dirname(self._critical_rules_file), exist_ok=True)
        with open(self._critical_rules_file, 'w', encoding='utf-8') as f:
            json.dump(self._critical_rules, f, ensure_ascii=False, indent=2)

    def store_critical_rule(self, text: str, metadata: dict = None) -> str:
        """Store a critical rule. Never compressed, always injected.

        Args:
            text: Rule content text
            metadata: Optional metadata dict

        Returns:
            rule_id: Unique rule identifier
        """
        rule_id = str(uuid.uuid4())[:8]
        self._critical_rules[rule_id] = {
            "id": rule_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        self._save_critical_rules()
        return rule_id

    def get_critical_rules(self) -> List[dict]:
        """Get all critical rules.

        Returns:
            List of critical rule dicts
        """
        return list(self._critical_rules.values())

    def delete_critical_rule(self, rule_id: str) -> bool:
        """Delete a critical rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            True if deleted, False if not found
        """
        if rule_id in self._critical_rules:
            del self._critical_rules[rule_id]
            self._save_critical_rules()
            return True
        return False

    def start_session(self, session_id: str, initial_context: Optional[str] = None) -> None:
        """
        Start new session

        Args:
            session_id: Session ID
            initial_context: Optional initial context for memory retrieval
        """
        self.session_id = session_id
        self.session_start = datetime.now()
        self.working_memory = []
        self.working_cache.clear()

        # Load all memories and build index
        self._load_and_build_index()

        # Use three-tier retrieval to find relevant memories based on context
        if initial_context:
            self._retrieve_contextual_memories(initial_context)

        # Load relevant memories to working memory (L1 cache)
        self._load_relevant_memories()

        # Create checkpoint
        self.checkpoint.create(session_id)

        # Log audit
        self.audit.log("session_start", {"session_id": session_id})

        _log(f"✅ Session {session_id} started, indexed {len(self.working_memory)} memories")

    def _retrieve_contextual_memories(self, context: str) -> None:
        """
        Retrieve contextual memories using three-tier retrieval

        Args:
            context: Session context or topic
        """
        results = self.cross_session_search(
            query=context,
            layers=["l2", "l3"],  # Search short-term and long-term memory
            limit=5,
        )

        if results:
            _log(f"🔍 Retrieved {len(results)} contextual memories for: {context[:50]}")

            # Add retrieved memories to working cache for quick access
            for result in results:
                memory_record = {
                    "id": result.get("memory_id"),
                    "content": result.get("content"),
                    "type": result.get("memory_type", "episodic"),
                    "tags": result.get("tags", []),
                    "timestamp": result.get("timestamp"),
                    "source": result.get("source"),
                    "layer": result.get("layer"),
                }
                if memory_record["id"]:
                    self.working_cache.put(memory_record["id"], memory_record)
        else:
            _log(f"ℹ️  No contextual memories found for: {context[:50]}")
    
    def end_session(self) -> None:
        """
        End session, auto-save memories
        """
        if not self.session_id:
            return
        
        # Save working memory to short-term memory
        self._save_working_memory()
        
        # Create checkpoint
        self.checkpoint.save(self.session_id)
        
        # Log audit
        self.audit.log("session_end", {
            "session_id": self.session_id,
            "duration": str(datetime.now() - self.session_start)
        })
        
        _log(f"✅ Session {self.session_id} ended, memories saved")
        
        self.session_id = None
        self.session_start = None
        self.working_memory = []
        self.working_cache.clear()
    
    def store(self, content: str, memory_type: str = "episodic", 
              tags: Optional[List[str]] = None, metadata: Optional[Dict] = None, 
              update_index: bool = True) -> bool:
        """
        Store memory
        
        Args:
            content: Memory content
            memory_type: Memory type (episodic/semantic/procedural)
            tags: Tag list
            metadata: Optional metadata dictionary (e.g., {"neo_agent": "Tech", "neo_domain": "Work"})
            update_index: Update search index incrementally (default: True)
            
        Returns:
            bool: Success status
        """
        # v2.20.0: Parameter validation
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        if memory_type not in ("episodic", "semantic", "procedural"):
            raise ValueError(f"Invalid memory_type: {memory_type}")

        # Security validation
        if not self.validator.validate(content):
            _log(f"❌ Memory write validation failed: {content[:50]}...")
            self.audit.log("write_rejected", {
                "content": content[:100],
                "reason": "validation_failed"
            })
            return False

        # Write-Time Gating check (v2.3.0)
        if self.enable_gating and self.gating is not None:
            gating_item = {
                'content': content,
                'source': metadata.get('source', 'user') if metadata else 'user',
                'memory_type': memory_type,
                'context': metadata or {},
                'session_id': self.session_id
            }

            # Use gating to decide if should store
            gating_result = self.gating.write(gating_item)

            # Log gating decision
            self.audit.log("gating_decision", {
                "content": content[:100],
                "type": memory_type,
                "salience": gating_result.salience_score,
                "tier": gating_result.tier,
                "stored": gating_result.stored
            })

            # If gated to cold storage, we still store but may limit indexing
            if gating_result.tier == 'cold':
                update_index = False  # Skip indexing for cold storage
        
        import uuid
        
        # Create memory record with ID generated upfront
        memory_record = {
            "id": str(uuid.uuid4())[:8],  # Generate ID before storage
            "content": content,
            "type": memory_type,
            "tags": tags or [],
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        # Store to different locations based on type
        if memory_type == "episodic":
            self.episodic.store(memory_record)
        elif memory_type == "semantic":
            self.semantic.store(memory_record)
        elif memory_type == "procedural":
            self.procedural.store(memory_record)
        else:
            _log(f"❌ Unknown memory type: {memory_type}")
            return False
        
        # Add to working memory
        self.working_memory.append(memory_record)
        
        # Add to L1 cache
        memory_id = memory_record.get("id")
        if memory_id:
            self.working_cache.put(memory_id, memory_record)
            
            # Incrementally update index
            if update_index and self.index.built:
                self.index.add_memory(content, memory_id, save_async=True)

            # v2.15.0: Auto-index into EngramIndex
            if self.engram is not None and update_index:
                self.engram.index(memory_id, content)
        
        # Log audit
        self.audit.log("memory_stored", {
            "type": memory_type,
            "content": content[:100]
        })
        
        _log(f"✅ Memory stored ({memory_type}): {content[:50]}...")
        return True
    
    def _search_impl(self, query: str, all_memories: List[Dict],
                    search_mode: str, memory_type: Optional[str],
                    limit: int, expanded_query: Optional[str] = None) -> tuple:
        """Internal search logic. Returns (results, method_name).

        Uses expanded_query for BM25-based modes and original query for keyword mode.
        """
        # Use expanded query for BM25-based modes, original for keyword
        _q = expanded_query or query
        if search_mode == "bm25":
            results = self.bm25_retriever.search(
                _q, all_memories, limit=limit * 2, rank_by_importance=True
            )
            method = "bm25"
        elif search_mode == "hybrid":
            results = self.hybrid_retriever.search(
                _q, all_memories, limit=limit * 2
            )
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "hybrid_bm25"
        elif search_mode == "entity":
            results = self.entity_retriever.search(
                _q, all_memories, limit=limit * 2
            )
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "entity_enhanced"
        elif search_mode == "hybrid_entity":
            results = self.hybrid_entity_retriever.search(
                _q, all_memories, limit=limit * 2
            )
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "hybrid_entity"
        elif search_mode == "heuristic":
            results = self.heuristic_retriever.search(
                _q, all_memories, limit=limit * 2
            )
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "heuristic"
        elif search_mode == "smart":
            results = self.smart_retriever.search(
                _q, all_memories, limit=limit * 2, rank_by_importance=True
            )
            method = "smart"
        elif search_mode == "enhanced_smart":
            results = self.enhanced_smart_retriever.search(
                _q, all_memories, limit=limit * 2, rank_by_importance=True
            )
            method = "enhanced_smart"
        else:
            results = self.retriever.search(
                query, self.episodic, self.semantic, self.procedural,
                memory_type=memory_type, limit=limit * 2
            )
            method = "keyword"
        return results, method

    def search(self, query: str, memory_type: Optional[str] = None,
               metadata: Optional[Dict] = None, limit: int = 10,
               mode: Optional[str] = None,
               include_critical: bool = True) -> List[Dict]:
        """
        Retrieve memories using specified search mode.

        v2.9.0: Added query cache (fast path), synonym expansion (recall boost),
        and search statistics tracking.
        v2.13.0: Added critical_rules prepending (never compressed, always injected).

        Args:
            query: Search query
            memory_type: Memory type filter (optional)
            metadata: Optional metadata filter (e.g., {"neo_agent": "Tech"})
            limit: Number of results
            mode: Search mode - "keyword" | "bm25" | "hybrid" | "entity"
                  | "hybrid_entity" | "heuristic" | "smart" | "enhanced_smart"
                  (default: use self.search_mode)
            include_critical: Include critical rules prepended to results (default: True)

        Returns:
            List[Dict]: Memory records
        """
        # v2.20.0: Parameter validation
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if len(query) > 2000:
            raise QueryTooLongError(
                f"Query length {len(query)} exceeds 2000 chars"
            )
        if limit < 1:
            limit = 1

        cache_hit = False
        t0 = time.time()
        search_mode = mode or self.search_mode

        # v2.13.0: Gather critical rules (never cached, always prepended)
        critical_rules = []
        if include_critical:
            critical_rules = self.get_critical_rules()

        # v2.19.0: Check QueryCache first
        if self._query_cache is not None:
            cached_ids = self._query_cache.get(query)
            if cached_ids is not None:
                if self._performance_monitor:
                    self._performance_monitor.record_cache_hit()
                # Reconstruct results from cached IDs
                cached_results = []
                for mid in cached_ids[:limit]:
                    node = self.multi_graph.get_node(mid) if self.multi_graph else None
                    r = {
                        "id": mid,
                        "content": getattr(node, 'content', '')[:200] if node else f"[cached:{mid}]",
                        "score": 1.0,
                        "type": "cached",
                    }
                    if node:
                        md = getattr(node, 'metadata', None)
                        if md:
                            r["metadata"] = md
                        tags = getattr(node, 'tags', None)
                        if tags:
                            r["tags"] = tags
                    cached_results.append(r)
                return (critical_rules + cached_results)[:limit]
            if self._performance_monitor:
                self._performance_monitor.record_cache_miss()

        # v2.15.0: 优先使用 Engram + Spreading 检索管线
        # Graph required for metadata/tags in results
        if (self.decoupled_retriever and self.multi_graph
                and memory_type is None and metadata is None and mode is None):
            results = self.decoupled_retriever.search(
                query, top_k=limit,
                intent=getattr(self, 'search_mode', 'general'),
            )
            if results:
                # v2.19.0: Cache the results
                if self._query_cache is not None:
                    self._query_cache.set(query, [r["id"] for r in results])
                if self._performance_monitor:
                    latency = (time.time() - t0) * 1000
                    self._performance_monitor.record_search(latency)
                if self.search_stats:
                    latency = (time.time() - t0) * 1000
                    self.search_stats.record_search(latency, cache_hit=False)
                return (critical_rules + results[:limit])[:limit]

        # v2.9.0: Check query cache first
        if self.query_cache and metadata is None and memory_type is None:
            cached = self.query_cache.get(query, limit)
            if cached is not None:
                cache_hit = True
                if self.search_stats:
                    latency = (time.time() - t0) * 1000
                    self.search_stats.record_search(latency, cache_hit=True)
                # Prepend critical rules (not counted toward limit)
                return critical_rules + cached[:limit]

        # v2.9.0: Expand query with synonyms
        search_query = query
        if self.synonym_expander:
            search_query = self.synonym_expander.expand(query)

        # Gather all memories for search
        all_memories = []
        if memory_type is None or memory_type == "episodic":
            all_memories.extend(self.episodic.get_recent(limit * 3))
        if memory_type is None or memory_type == "semantic":
            all_memories.extend(self.semantic.get_all())
        if memory_type is None or memory_type == "procedural":
            all_memories.extend(self.procedural.get_all())

        # Perform search
        results, method = self._search_impl(
            query, all_memories, search_mode, memory_type, limit,
            expanded_query=search_query)

        # Apply metadata filter if specified
        if metadata:
            results = [
                m for m in results
                if all(m.get("metadata", {}).get(k) == v
                       for k, v in metadata.items())
            ]

        results = results[:limit]

        # v2.9.0: Cache results for future queries
        if self.query_cache and metadata is None and memory_type is None:
            self.query_cache.put(query, results, top_k=limit)

        # v2.9.0: Record statistics
        if self.search_stats:
            latency = (time.time() - t0) * 1000
            self.search_stats.record_search(latency, cache_hit=False)

        # Log audit
        self.audit.log("memory_search", {
            "query": query,
            "type": memory_type,
            "metadata": metadata,
            "results_count": len(results),
            "method": method
        })

        _log(f"🔍 Retrieved {len(results)} memories ({method}): {query}")

        # v2.13.0: Prepend critical rules (limited to requested count)
        return (critical_rules + results)[:limit]

    def cross_session_search(self, query: str,
                              layers: Optional[List[str]] = None,
                              limit: int = 10,
                              memory_type: Optional[str] = None) -> List[Dict]:
        """
        Cross-session memory search using three-tier retrieval

        Args:
            query: Search query
            layers: Layers to search ["l1", "l2", "l3"] (default: all)
            limit: Maximum results
            memory_type: Memory type filter

        Returns:
            List[Dict]: Memory result dictionaries
        """
        # Prepare session context for L1 search
        session_context = {
            "working_memory": self.working_memory,
            "session_id": self.session_id,
        }

        results = self.three_tier_retriever.search(
            query=query,
            layers=layers,
            limit=limit,
            memory_type=memory_type,
            session_context=session_context,
        )

        # Convert MemoryResult objects to dicts
        return [r.to_dict() for r in results]
    
    def _load_and_build_index(self) -> None:
        """
        Load all memories and build in-memory index
        Uses persisted index if available for fast startup
        """
        # Load all memories
        all_episodic = self.episodic.get_all()
        all_semantic = self.semantic.get_all()
        all_procedural = self.procedural.get_all()
        
        # Combine all memories
        all_memories = all_episodic + all_semantic + all_procedural
        
        # Load or build in-memory index (with persistence support)
        loaded_from_disk = self.index.load_or_build(all_memories)
        
        # Add to working memory
        self.working_memory = all_memories
        
        if loaded_from_disk:
            _log(f"📥 Index loaded from disk: {len(all_episodic)} Episodic, {len(all_semantic)} Semantic, {len(all_procedural)} Procedural")
        else:
            _log(f"📥 Indexed {len(all_episodic)} Episodic, {len(all_semantic)} Semantic, {len(all_procedural)} Procedural")
    
    def _load_relevant_memories(self) -> None:
        """
        Load relevant memories to working memory (L1 cache)
        """
        # Cache recent Episodic and all Semantic memories
        recent_episodic = self.episodic.get_recent(limit=20)
        all_semantic = self.semantic.get_all()
        
        for memory in recent_episodic + all_semantic:
            memory_id = memory.get("id")
            if memory_id:
                self.working_cache.put(memory_id, memory)
        
        _log(f"💾 Cached {len(recent_episodic) + len(all_semantic)} memories in L1")
    
    def _save_working_memory(self) -> None:
        """
        Save working memory to short-term memory
        """
        # Save working memory as Episodic memory
        if self.working_memory:
            content = "\n".join([m["content"] for m in self.working_memory])
            self.store(content, memory_type="episodic")
    
    def get_stats(self) -> Dict:
        """
        Get memory statistics

        Returns:
            Dict: Statistics (includes graph/decay/ground_truth in v2.14.0)
        """
        stats = {
            "workspace": str(self.workspace),
            "session_id": self.session_id,
            "working_memory_count": len(self.working_memory),
            "working_cache_size": self.working_cache.size(),
            "index_built": self.index.built,
            "episodic_count": self.episodic.count(),
            "semantic_count": self.semantic.count(),
            "procedural_count": self.procedural.count(),
        }
        # v2.14.0 additions
        mg = self.multi_graph
        if mg:
            stats["graph"] = mg.get_stats()
        ctrl = self.decay_controller
        if ctrl:
            stats["decay"] = ctrl.get_stats()
        gt = self.ground_truth
        if gt:
            stats["ground_truth"] = {
                "sessions": len(gt.list_sessions()),
                "records": gt.count_records(),
            }
        return stats

    def get_gating_stats(self) -> Optional[Dict]:
        """
        Get gating statistics

        Returns:
            Dict: Gating statistics or None if gating is disabled
        """
        if not self.enable_gating or self.gating is None:
            return None

        return self.gating.get_stats()

    # ── v2.14.0: Graph + Decay + GroundTruth properties ───────────────

    @property
    def multi_graph(self) -> Optional[MultiGraphMemory]:
        if self._multi_graph is None and self.enable_graph:
            self._multi_graph = MultiGraphMemory()
        return self._multi_graph

    @property
    def dual_layer(self) -> Optional[DualLayerMemory]:
        if self._dual_layer is None and self.enable_graph:
            self._dual_layer = DualLayerMemory()
        return self._dual_layer

    @property
    def decay_controller(self) -> Optional[DecayController]:
        if self._decay_controller is None and self.enable_decay and self.multi_graph:
            self._decay_controller = DecayController(
                self.multi_graph, config=self._decay_config
            )
        return self._decay_controller

    @property
    def decay_scheduler(self) -> Optional[DecayScheduler]:
        if self._decay_scheduler is None and self.enable_decay and self.decay_controller:
            self._decay_scheduler = DecayScheduler(
                self.decay_controller, config=self._decay_config
            )
            self._decay_scheduler.start()
        return self._decay_scheduler

    @property
    def ground_truth(self) -> Optional[GroundTruthStore]:
        if self._ground_truth is None and self.enable_ground_truth:
            self._ground_truth = GroundTruthStore(str(self.workspace))
        return self._ground_truth

    # ── v2.14.0: Graph operations ──────────────────────────────────────

    def get_graph_stats(self) -> dict:
        """Get graph structure statistics."""
        mg = self.multi_graph
        if mg is None:
            return {"enabled": False}
        stats = mg.get_stats()
        stats["enabled"] = True
        return stats

    def get_node_graph(self, memory_id: str) -> dict:
        """Get a node's relationships across all subgraphs."""
        mg = self.multi_graph
        if mg is None:
            return {"error": "Graph not enabled"}
        node = mg.get_node(memory_id)
        if node is None:
            return {"error": f"Node not found: {memory_id}"}
        neighbors = {}
        for sg_type in list(mg._graphs.keys()):
            neighbors[sg_type.value] = [
                {"id": nid, "weight": w}
                for nid, w in mg._graphs[sg_type].get_neighbors(
                    memory_id, max_depth=1
                ).items()
            ]
        return {"node": node.to_dict(), "neighbors": neighbors}

    def persist_graph(self) -> bool:
        """Manually persist graph structure to disk."""
        mg = self.multi_graph
        if mg is None:
            return False
        try:
            d = mg.to_dict()
            gpath = os.path.join(
                os.path.expanduser("~/.claw-mem"), "graph_index.json"
            )
            os.makedirs(os.path.dirname(gpath), exist_ok=True)
            with open(gpath, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    # ── v2.14.0: Decay operations ──────────────────────────────────────

    def get_decay_stats(self) -> dict:
        """Get decay statistics."""
        ctrl = self.decay_controller
        if ctrl is None:
            return {"enabled": False}
        stats = ctrl.get_stats()
        stats["enabled"] = True
        return stats

    def force_decay_cycle(self) -> int:
        """Force an immediate decay cycle."""
        ctrl = self.decay_controller
        if ctrl is None:
            return 0
        updates = ctrl.compute_all_decays()
        if updates:
            ctrl._graph.apply_decay(updates)
        removed = ctrl.cleanup_expired()
        return len(removed)

    # ── v2.14.0: GroundTruth operations ────────────────────────────────

    def search_ground_truth(self, session_id: str = None,
                            keyword: str = None,
                            limit: int = 50) -> List[Dict]:
        """Search raw conversation transcripts."""
        gt = self.ground_truth
        if gt is None:
            return []
        return gt.search(session_id=session_id, keyword=keyword, limit=limit)

    def list_sessions(self) -> List[Dict]:
        """List all stored sessions."""
        gt = self.ground_truth
        if gt is None:
            return []
        return gt.list_sessions()

    # ── v2.15.0: Engram + Spreading + Decoupled properties ──────────

    @property
    def engram(self) -> Optional[EngramIndex]:
        if self._engram is None and self.enable_engram:
            self._engram = EngramIndex(ngram_size=self._engram_ngram_size)
        return self._engram

    @property
    def spreader(self) -> Optional[SpreadingActivation]:
        if self._spreader is None and self.enable_spreading and self.multi_graph:
            self._spreader = SpreadingActivation(self.multi_graph)
            self._spreader.configure(
                max_depth=self._spreading_max_depth,
                decay_factor=self._spreading_decay_factor,
                threshold=self._spreading_threshold,
            )
        return self._spreader

    @property
    def decoupled_retriever(self) -> Optional[DecoupledRetriever]:
        if self._decoupled_retriever is None and self.engram:
            self._decoupled_retriever = DecoupledRetriever(
                self.engram, self.spreader, self.multi_graph
            )
        return self._decoupled_retriever

    @property
    def compression_spectrum(self) -> Optional[CompressionSpectrum]:
        if self._compression_spectrum is None and self.enable_compression_spectrum:
            self._compression_spectrum = CompressionSpectrum(
                self,
                access_threshold=self._compression_trigger_access,
                apply_threshold=self._compression_trigger_apply,
                verify_threshold=self._compression_trigger_verify,
            )
        return self._compression_spectrum

    # ── v2.15.0: Operations ──────────────────────────────────────────

    def get_engram_stats(self) -> dict:
        e = self.engram
        return e.get_stats() if e else {"enabled": False}

    def rebuild_engram(self) -> int:
        e = self.engram
        if e is None:
            return 0
        count = 0
        if hasattr(self, 'index') and self.index.built:
            for mid, doc in zip(self.index.memory_ids, self.index.documents):
                content = ' '.join(doc) if isinstance(doc, list) else str(doc)
                e.index(mid, content)
                count += 1
        return count

    def get_spreading_stats(self) -> dict:
        s = self.spreader
        return s.get_stats() if s else {"enabled": False}

    def get_compression_stats(self) -> dict:
        c = self.compression_spectrum
        return c.get_stats() if c else {"enabled": False}

    def manual_compress(self, memory_id: str) -> Optional[Dict]:
        c = self.compression_spectrum
        if c is None:
            return None
        result = c.record_access(memory_id)
        return result.__dict__ if result else None

    # ── v2.19.0: Performance monitor ──────────────────────────────

    @property
    def performance_monitor(self) -> Optional[PerformanceMonitor]:
        if self._performance_monitor is None:
            self._performance_monitor = PerformanceMonitor()
        return self._performance_monitor

    # ── v3.0.0-rc.1: CMS Perception Layer ──────────────────────

    @property
    def cms_capacity(self) -> Optional[CapacityMonitor]:
        if self._cms_capacity is None and self.enable_cms:
            self._cms_capacity = CapacityMonitor(
                self,
                token_threshold=self._cms_token_threshold,
                memory_threshold=self._cms_memory_threshold,
                warning_level=self._cms_warning_level,
            )
        return self._cms_capacity

    @property
    def cms_hook(self) -> Optional[ContextWarningHook]:
        if self._cms_hook is None and self.cms_capacity:
            self._cms_hook = ContextWarningHook(self.cms_capacity)
        return self._cms_hook

    @property
    def cms_importance(self) -> Optional[ImportanceEvaluator]:
        if self._cms_importance is None and self.enable_cms:
            self._cms_importance = ImportanceEvaluator(self)
        return self._cms_importance

    def get_capacity_stats(self) -> Optional[dict]:
        c = self.cms_capacity
        if c is None:
            return None
        return c.get_stats().to_dict()

    def get_importance_scores(self, memory_ids: List[str]) -> Optional[Dict]:
        i = self.cms_importance
        if i is None:
            return None
        return {k: v.to_dict() for k, v in i.evaluate_batch(memory_ids).items()}

    def get_important_memories(self, threshold: float = 0.5,
                               limit: int = 50) -> Optional[List]:
        i = self.cms_importance
        if i is None:
            return None
        return [s.to_dict() for s in i.get_important_memories(threshold, limit)]

    # ── v3.0.0-rc.2: Compression layer ────────────────────────

    @property
    def cms_summarizer(self) -> Optional[SessionSummaryGenerator]:
        if self._cms_summarizer is None and self.enable_cms:
            self._cms_summarizer = SessionSummaryGenerator()
        return self._cms_summarizer

    @property
    def cms_deduplicator(self) -> Optional[MemoryDeduplicator]:
        if self._cms_deduplicator is None and self.enable_cms:
            self._cms_deduplicator = MemoryDeduplicator(self)
        return self._cms_deduplicator

    @property
    def cms_strategy(self) -> Optional[CompressionStrategySelector]:
        if self._cms_strategy is None and self.enable_cms:
            self._cms_strategy = CompressionStrategySelector()
        return self._cms_strategy

    def generate_summary(self, session_id: str,
                         memories: List[Dict] = None,
                         strategy: str = "key_points") -> Optional[dict]:
        s = self.cms_summarizer
        if s is None:
            return None
        if memories is None:
            memories = []
        return s.generate(session_id, memories, strategy).to_dict()

    def deduplicate_memories(self, memory_ids: List[str],
                             threshold: float = 0.85) -> Optional[dict]:
        d = self.cms_deduplicator
        if d is None:
            return None
        d._similarity_threshold = threshold
        return d.deduplicate(memory_ids).to_dict()

    def compress_session(self, session_id: str,
                         strategy: str = "auto") -> Optional[dict]:
        if not self.enable_cms:
            return None
        import time as _time
        t0 = _time.time()

        # Get capacity info
        stats = self.get_capacity_stats()
        utilization = stats.get("utilization", 0.5) if stats else 0.5

        # Select strategy
        sel = self.cms_strategy
        if strategy == "auto":
            plan = sel.select(utilization) if sel else None
        else:
            plan = sel.select(0.99 if strategy == "aggressive"
                              else 0.8 if strategy == "balanced"
                              else 0.5) if sel else None

        if plan is None:
            return None

        # Gather memories for this session
        memories = self._gather_session_memories(session_id)

        # Execute plan
        summary = None
        dedup = None

        if "summarize" in plan.suggested_actions:
            s = self.cms_summarizer
            if s:
                summary = s.generate(session_id, memories)
        if "deduplicate" in plan.suggested_actions:
            d = self.cms_deduplicator
            if d:
                mem_ids = [m.get("id", "") for m in memories if m.get("id")]
                dedup = d.deduplicate(mem_ids)

        original_tokens = sum(len(m.get("content", "").split()) for m in memories)
        final_tokens = original_tokens
        if dedup:
            final_tokens = int(original_tokens * (1 - dedup.reduction_ratio))

        elapsed = (_time.time() - t0) * 1000
        result = CompressionResult(
            session_id=session_id,
            plan=plan,
            summary=summary,
            dedup=dedup,
            original_token_count=original_tokens,
            final_token_count=final_tokens,
            reduction_ratio=1.0 - final_tokens / max(1, original_tokens),
            execution_time_ms=elapsed,
        )
        return result.to_dict()

    # ── v3.0.0-rc.3: State Machine ───────────────────────────────

    @property
    def cms_snap_storage(self) -> Optional[SnapshotStorage]:
        if not hasattr(self, '_cms_snap'):
            self._cms_snap = SnapshotStorage(str(self.workspace))
        return self._cms_snap

    def get_session_state(self, session_id: str) -> str:
        if not hasattr(self, '_cms_state_machine'):
            self._cms_state_machine = SessionStateMachine()
        return self._cms_state_machine.get_current_state(session_id)

    def set_session_state(self, session_id: str, state: str) -> None:
        if not hasattr(self, '_cms_state_machine'):
            self._cms_state_machine = SessionStateMachine()
        self._cms_state_machine.set_state(session_id, state)

    def save_snapshot(self, session_id: str) -> str:
        s = self.cms_snap_storage
        mem_ids = []
        for m in self._gather_session_memories(session_id):
            mid = m.get("id", "")
            if mid:
                mem_ids.append(mid)
        return s.save(session_id, state="active", memory_ids=mem_ids)

    def load_snapshot(self, snapshot_id: str) -> Optional[dict]:
        s = self.cms_snap_storage
        snap = s.load(snapshot_id)
        return snap.to_dict() if snap else None

    def list_snapshots(self, session_id: str) -> List:
        return [
            {"snapshot_id": i.snapshot_id, "timestamp": i.timestamp.isoformat(),
             "state": i.state, "size_bytes": i.size_bytes}
            for i in self.cms_snap_storage.list(session_id)
        ]

    def delete_snapshot(self, snapshot_id: str) -> bool:
        return self.cms_snap_storage.delete(snapshot_id)

    def switch_context(self, from_id: str, to_id: str,
                       strategy: str = "preserve_important") -> Optional[dict]:
        switcher = ContextSwitcher(
            importance_evaluator=self.cms_importance, memory_manager=self
        )
        return switcher.switch(from_id, to_id, strategy).to_dict()

    def recover_session(self, session_id: str,
                        snapshot_id: str = None,
                        strategy: str = "latest") -> Optional[dict]:
        recovery = RecoveryMechanism(
            snapshot_storage=self.cms_snap_storage, memory_manager=self
        )
        return recovery.recover(session_id, snapshot_id, strategy).to_dict()

    def _gather_session_memories(self, session_id: str) -> List[Dict]:
        memories = []
        try:
            episodic = self.episodic.get_all() if hasattr(self, 'episodic') else []
            memories.extend(episodic)
        except Exception:
            pass
        return memories

    def get_performance_stats(self) -> dict:
        pm = self.performance_monitor
        stats = pm.get_stats() if pm else {"enabled": False}
        if self._query_cache:
            stats["cache"] = self._query_cache.stats()
        return stats

    def __repr__(self) -> str:
        return f"MemoryManager(workspace={self.workspace}, session={self.session_id})"
