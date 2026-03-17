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
from .retrieval.keyword import KeywordRetriever
from .security.validation import WriteValidator
from .security.checkpoint import CheckpointManager
from .security.audit import AuditLogger


class MemoryManager:
    """
    Memory Manager
    
    Core responsibilities:
    1. Manage three-layer memory architecture
    2. Provide storage and retrieval interfaces
    3. Auto-save and load
    4. Security validation and auditing
    """
    
    def __init__(self, workspace: str = "~/.openclaw/workspace"):
        """
        Initialize Memory Manager
        
        Args:
            workspace: OpenClaw workspace path
        """
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
        
        # Working memory (L1)
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
        
        # Load relevant memories
        self._load_relevant_memories()
        
        # Create checkpoint
        self.checkpoint.create(session_id)
        
        # Log audit
        self.audit.log("session_start", {"session_id": session_id})
        
        print(f"✅ Session {session_id} started, loaded {len(self.working_memory)} memories")
    
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
    
    def store(self, content: str, memory_type: str = "episodic", 
              tags: Optional[List[str]] = None) -> bool:
        """
        Store memory
        
        Args:
            content: Memory content
            memory_type: Memory type (episodic/semantic/procedural)
            tags: Tag list
            
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
        Retrieve memories
        
        Args:
            query: Search query
            memory_type: Memory type filter (optional)
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records
        """
        # Search using retriever
        results = self.retriever.search(
            query=query,
            episodic=self.episodic,
            semantic=self.semantic,
            procedural=self.procedural,
            memory_type=memory_type,
            limit=limit
        )
        
        # Log audit
        self.audit.log("memory_search", {
            "query": query,
            "type": memory_type,
            "results_count": len(results)
        })
        
        print(f"🔍 Retrieved {len(results)} memories: {query}")
        return results
    
    def _load_relevant_memories(self) -> None:
        """
        Load relevant memories to working memory
        """
        # MVP version: Load recent Episodic and all Semantic memories
        recent_episodic = self.episodic.get_recent(limit=20)
        all_semantic = self.semantic.get_all()
        
        self.working_memory.extend(recent_episodic)
        self.working_memory.extend(all_semantic)
        
        print(f"📥 Loaded {len(recent_episodic)} Episodic memories, {len(all_semantic)} Semantic memories")
    
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
            "episodic_count": self.episodic.count(),
            "semantic_count": self.semantic.count(),
            "procedural_count": self.procedural.count(),
        }
    
    def __repr__(self) -> str:
        return f"MemoryManager(workspace={self.workspace}, session={self.session_id})"
