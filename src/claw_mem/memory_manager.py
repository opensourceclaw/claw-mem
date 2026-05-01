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
from .security.validation import WriteValidator
from .security.checkpoint import CheckpointManager
from .security.audit import AuditLogger
from .config import ConfigDetector
from .importance import ImportanceScorer
from .memory_fix_plugin import MemoryFixPlugin
from .memory_decay import MemoryDecay
from .rule_extractor import RuleExtractor
from .gating import WriteTimeGating


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
                 recency_boost: float = 1.0, frequency_boost: float = 1.0):
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
        
        # Initialize storage layers
        self.episodic = EpisodicStorage(self.workspace)
        self.semantic = SemanticStorage(self.workspace)
        self.procedural = ProceduralStorage(self.workspace)
        
        # Initialize utilities
        self.retriever = KeywordRetriever()
        self.bm25_retriever = BM25Retriever(
            k1=bm25_k1, b=bm25_b,
            recency_boost=recency_boost, frequency_boost=frequency_boost
        )
        self.hybrid_retriever = HybridBM25Retriever(
            k1=bm25_k1, b=bm25_b,
            bm25_weight=bm25_weight, keyword_weight=keyword_weight,
            recency_boost=recency_boost, frequency_boost=frequency_boost
        )
        self.entity_retriever = EntityEnhancedRetriever(use_spacy=False)  # Fallback mode
        self.hybrid_entity_retriever = HybridEntityRetriever(use_spacy=False)  # Fallback mode
        self.heuristic_retriever = HeuristicRetriever()
        self.smart_retriever = SmartRetriever()
        self.enhanced_smart_retriever = EnhancedSmartRetriever()
        self.three_tier_retriever = ThreeTierRetriever(self.workspace)
        self.session_startup_hook = SessionStartupHook(self.three_tier_retriever)
        self.validator = WriteValidator()
        self.checkpoint = CheckpointManager(self.workspace)
        self.audit = AuditLogger(self.workspace)
        self.importance_scorer = ImportanceScorer()
        
        # Initialize memory fix plugin (F000)
        self.memory_fix = MemoryFixPlugin(self.workspace)
        
        # Initialize memory decay (F102)
        self.memory_decay = MemoryDecay(self.workspace)
        
        # Initialize rule extractor (F101)
        self.rule_extractor = RuleExtractor(self.workspace)

        # Initialize Write-Time Gating (v2.1.0)
        self.enable_gating = enable_gating
        self.gating_threshold = gating_threshold
        self.gating = WriteTimeGating(threshold=gating_threshold) if enable_gating else None

        # Initialize Concept-Mediated Graph (v2.2.0)
        self.enable_graph = enable_graph
        self.graph = None
        if enable_graph:
            from claw_mem.graph import ConceptMediatedGraph, DummyEmbedder, KeywordExtractor
            self.graph = ConceptMediatedGraph(
                embedder=DummyEmbedder(),
                extractor=KeywordExtractor()
            )

        # Search mode: "keyword" | "bm25" | "hybrid" | "entity" | "hybrid_entity" | "heuristic" | "smart" | "enhanced_smart"
        self.search_mode = os.environ.get('CLAW_MEM_SEARCH_MODE', 'enhanced_smart')
        
        # Validate session memory on startup
        self._validate_session_memory()
    
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
        
        # Log audit
        self.audit.log("memory_stored", {
            "type": memory_type,
            "content": content[:100]
        })
        
        _log(f"✅ Memory stored ({memory_type}): {content[:50]}...")
        return True
    
    def search(self, query: str, memory_type: Optional[str] = None,
               metadata: Optional[Dict] = None, limit: int = 10,
               mode: Optional[str] = None) -> List[Dict]:
        """
        Retrieve memories using specified search mode.

        Args:
            query: Search query
            memory_type: Memory type filter (optional)
            metadata: Optional metadata filter (e.g., {"neo_agent": "Tech"})
            limit: Number of results
            mode: Search mode - "keyword" | "bm25" | "hybrid" | "entity" | "hybrid_entity" (default: use self.search_mode)

        Returns:
            List[Dict]: Memory records
        """
        # Use provided mode or default
        search_mode = mode or self.search_mode
        
        # Gather all memories for BM25/Entity search
        all_memories = []
        if memory_type is None or memory_type == "episodic":
            all_memories.extend(self.episodic.get_recent(limit * 3))
        if memory_type is None or memory_type == "semantic":
            all_memories.extend(self.semantic.get_all())
        if memory_type is None or memory_type == "procedural":
            all_memories.extend(self.procedural.get_all())
        
        # Choose search strategy
        if search_mode == "bm25":
            # Pure BM25 search
            results = self.bm25_retriever.search(
                query, all_memories, limit=limit * 2, rank_by_importance=True
            )
            method = "bm25"
        elif search_mode == "hybrid":
            # Hybrid BM25 + keyword search
            results = self.hybrid_retriever.search(
                query, all_memories, limit=limit * 2
            )
            # Apply importance ranking
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "hybrid_bm25"
        elif search_mode == "entity":
            # Entity-enhanced search
            results = self.entity_retriever.search(
                query, all_memories, limit=limit * 2
            )
            # Apply importance ranking
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "entity_enhanced"
        elif search_mode == "hybrid_entity":
            # Hybrid BM25 + Entity + Keyword search (recommended)
            results = self.hybrid_entity_retriever.search(
                query, all_memories, limit=limit * 2
            )
            # Apply importance ranking
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "hybrid_entity"
        elif search_mode == "heuristic":
            # Heuristic search (BM25 + Entity + Time + Type + Keyword)
            results = self.heuristic_retriever.search(
                query, all_memories, limit=limit * 2
            )
            # Apply importance ranking
            if results:
                results = self.importance_scorer.rank_memories(results)
            method = "heuristic"
        elif search_mode == "smart":
            # Smart search (all features enabled)
            results = self.smart_retriever.search(
                query, all_memories, limit=limit * 2, rank_by_importance=True
            )
            method = "smart"
        elif search_mode == "enhanced_smart":
            # Enhanced smart search (with time parsing and preference detection)
            results = self.enhanced_smart_retriever.search(
                query, all_memories, limit=limit * 2, rank_by_importance=True
            )
            method = "enhanced_smart"
        else:
            # Fallback to keyword search (original behavior)
            results = self.retriever.search(
                query, self.episodic, self.semantic, self.procedural,
                memory_type=memory_type, limit=limit * 2
            )
            method = "keyword"
        
        # Apply metadata filter if specified
        if metadata:
            filtered_results = []
            for memory in results:
                memory_metadata = memory.get("metadata", {})
                if all(memory_metadata.get(k) == v for k, v in metadata.items()):
                    filtered_results.append(memory)
            results = filtered_results
        
        # Log audit
        self.audit.log("memory_search", {
            "query": query,
            "type": memory_type,
            "metadata": metadata,
            "results_count": len(results),
            "method": method
        })

        _log(f"🔍 Retrieved {len(results)} memories ({method}): {query}")
        return results[:limit]

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
            Dict: Statistics
        """
        return {
            "workspace": str(self.workspace),
            "session_id": self.session_id,
            "working_memory_count": len(self.working_memory),
            "working_cache_size": self.working_cache.size(),
            "index_built": self.index.built,
            "episodic_count": self.episodic.count(),
            "semantic_count": self.semantic.count(),
            "procedural_count": self.procedural.count(),
        }

    def get_gating_stats(self) -> Optional[Dict]:
        """
        Get gating statistics

        Returns:
            Dict: Gating statistics or None if gating is disabled
        """
        if not self.enable_gating or self.gating is None:
            return None

        return self.gating.get_stats()

    def __repr__(self) -> str:
        return f"MemoryManager(workspace={self.workspace}, session={self.session_id})"
