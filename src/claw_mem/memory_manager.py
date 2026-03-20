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
from .security.validation import WriteValidator
from .security.checkpoint import CheckpointManager
from .security.audit import AuditLogger
from .config import ConfigDetector
from .importance import ImportanceScorer
from .memory_fix_plugin import MemoryFixPlugin
from .memory_decay import MemoryDecay
from .rule_extractor import RuleExtractor


class MemoryManager:
    """
    Memory Manager
    
    Core responsibilities:
    1. Manage three-layer memory architecture
    2. Provide storage and retrieval interfaces
    3. Auto-save and load
    4. Security validation and auditing
    """
    
    def __init__(self, workspace: Optional[str] = None, auto_detect: bool = True):
        """
        Initialize Memory Manager
        
        Args:
            workspace: OpenClaw workspace path (optional, auto-detect if None)
            auto_detect: Enable auto-detection (default: True)
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
        
        # Validate session memory on startup
        self._validate_session_memory()
    
    def _validate_session_memory(self):
        """验证会话启动时的记忆（F000 修复）"""
        validation = self.memory_fix.validate_session_memory()
        
        if not validation['valid']:
            # 记录错误但不阻止启动
            self.audit.log("MEMORY_VALIDATION_FAILED", str(validation['errors']))
        
        if validation['warnings']:
            # 记录警告
            for warning in validation['warnings']:
                self.audit.log("MEMORY_WARNING", warning)
        
        # L1: Working Memory (In-Memory Index + Cache)
        # Enable index persistence for fast startup
        self.index = InMemoryIndex(ngram_size=3, enable_persistence=True)
        self.working_cache = WorkingMemoryCache(max_size=100, ttl_seconds=300)
        self.working_memory: List[Dict] = []
        
        print(f"🧠 claw-mem initialized, workspace: {self.workspace}")
    
    def start_session(self, session_id: str) -> None:
        """
        Start new session
        
        Args:
            session_id: Session ID
        """
        self.session_id = session_id
        self.session_start = datetime.now()
        self.working_memory = []
        self.working_cache.clear()
        
        # Load all memories and build index
        self._load_and_build_index()
        
        # Load relevant memories to working memory (L1 cache)
        self._load_relevant_memories()
        
        # Create checkpoint
        self.checkpoint.create(session_id)
        
        # Log audit
        self.audit.log("session_start", {"session_id": session_id})
        
        print(f"✅ Session {session_id} started, indexed {len(self.working_memory)} memories")
    
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
        
        print(f"✅ Session {self.session_id} ended, memories saved")
        
        self.session_id = None
        self.session_start = None
        self.working_memory = []
        self.working_cache.clear()
    
    def store(self, content: str, memory_type: str = "episodic", 
              tags: Optional[List[str]] = None, update_index: bool = True) -> bool:
        """
        Store memory
        
        Args:
            content: Memory content
            memory_type: Memory type (episodic/semantic/procedural)
            tags: Tag list
            update_index: Update search index incrementally (default: True)
            
        Returns:
            bool: Success status
        """
        # Security validation
        if not self.validator.validate(content):
            print(f"❌ Memory write validation failed: {content[:50]}...")
            self.audit.log("write_rejected", {
                "content": content[:100],
                "reason": "validation_failed"
            })
            return False
        
        # Create memory record
        memory_record = {
            "content": content,
            "type": memory_type,
            "tags": tags or [],
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
            print(f"❌ Unknown memory type: {memory_type}")
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
        
        print(f"✅ Memory stored ({memory_type}): {content[:50]}...")
        return True
    
    def search(self, query: str, memory_type: Optional[str] = None, 
               limit: int = 10) -> List[Dict]:
        """
        Retrieve memories using hybrid search (N-gram + BM25)
        
        Args:
            query: Search query
            memory_type: Memory type filter (optional)
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records
        """
        # Use in-memory index for fast search
        if self.index.built:
            hybrid_results = self.index.hybrid_search(query, limit=limit)
            
            # Convert memory_ids to memory records
            results = []
            for memory_id, score in hybrid_results:
                # Check L1 cache first
                cached = self.working_cache.get(memory_id)
                if cached:
                    results.append(cached)
                else:
                    # Find from working memory
                    for memory in self.working_memory:
                        if memory.get("id") == memory_id:
                            results.append(memory)
                            # Add to cache
                            self.working_cache.put(memory_id, memory)
                            break
            
            # Log audit
            self.audit.log("memory_search", {
                "query": query,
                "type": memory_type,
                "results_count": len(results),
                "method": "hybrid_index"
            })
            
            print(f"🔍 Retrieved {len(results)} memories (hybrid): {query}")
            return results
        else:
            # Fallback to keyword search
            results = self.retriever.search(
                query=query,
                episodic=self.episodic,
                semantic=self.semantic,
                procedural=self.procedural,
                memory_type=memory_type,
                limit=limit
            )
            
            print(f"🔍 Retrieved {len(results)} memories (keyword): {query}")
            return results
    
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
            print(f"📥 Index loaded from disk: {len(all_episodic)} Episodic, {len(all_semantic)} Semantic, {len(all_procedural)} Procedural")
        else:
            print(f"📥 Indexed {len(all_episodic)} Episodic, {len(all_semantic)} Semantic, {len(all_procedural)} Procedural")
    
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
        
        print(f"💾 Cached {len(recent_episodic) + len(all_semantic)} memories in L1")
    
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
    
    def __repr__(self) -> str:
        return f"MemoryManager(workspace={self.workspace}, session={self.session_id})"
