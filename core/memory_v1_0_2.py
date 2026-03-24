"""
claw-mem Memory System v1.0.2

Enhanced memory system with critical rule tagging, confidence scoring,
and source tracking.

License: Apache-2.0
Documentation Language: 100% English (Apache Standard)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
import json
from pathlib import Path


@dataclass
class Memory:
    """Memory representation with v1.0.2 enhancements"""
    
    # Core fields (existing)
    id: str
    content: str
    tags: List[str] = field(default_factory=list)
    
    # NEW: Priority & Critical Rule (v1.0.2)
    is_critical: bool = False
    priority: int = 3  # 1-5 (5=critical, 3=normal, 1=low)
    
    # NEW: Confidence Scoring (v1.0.2)
    confidence: float = 0.5  # 0.0-1.0 (50% default)
    
    # NEW: Source Tracking (v1.0.2)
    source: str = 'inferred'  # 'user' | 'inferred' | 'system'
    
    # Metadata (existing)
    created_at: datetime = field(default_factory=datetime.now)
    reinforced_at: Optional[datetime] = None
    
    # NEW: Usage Tracking (v1.0.2)
    use_count: int = 0
    success_count: int = 0
    flagged_for_review: bool = False
    
    def reinforce(self, success: bool):
        """Reinforce memory based on outcome"""
        self.use_count += 1
        if success:
            self.success_count += 1
            self.confidence = min(1.0, self.confidence + 0.05)
        else:
            self.confidence = max(0.0, self.confidence - 0.2)
            self.flagged_for_review = True
        self.reinforced_at = datetime.now()
    
    def mark_critical(self):
        """Mark as critical rule"""
        self.is_critical = True
        self.priority = 5
        self.source = 'user'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'content': self.content,
            'tags': self.tags,
            'is_critical': self.is_critical,
            'priority': self.priority,
            'confidence': self.confidence,
            'source': self.source,
            'created_at': self.created_at.isoformat(),
            'reinforced_at': self.reinforced_at.isoformat() if self.reinforced_at else None,
            'use_count': self.use_count,
            'success_count': self.success_count,
            'flagged_for_review': self.flagged_for_review,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Memory':
        """Create from dictionary (with backward compatibility)"""
        return cls(
            id=data['id'],
            content=data['content'],
            tags=data.get('tags', []),
            is_critical=data.get('is_critical', False),
            priority=data.get('priority', 3),
            confidence=data.get('confidence', 0.5),
            source=data.get('source', 'inferred'),
            created_at=datetime.fromisoformat(data['created_at']),
            reinforced_at=datetime.fromisoformat(data['reinforced_at']) if data.get('reinforced_at') else None,
            use_count=data.get('use_count', 0),
            success_count=data.get('success_count', 0),
            flagged_for_review=data.get('flagged_for_review', False),
        )


class MemorySystem:
    """Memory system with v1.0.2 enhancements"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.memories: Dict[str, Memory] = {}
        self._load_all()
    
    def _load_all(self):
        """Load all memories from storage"""
        if not self.storage_path.exists():
            return
        
        for file in self.storage_path.glob('*.json'):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    memory = Memory.from_dict(data)
                    self.memories[memory.id] = memory
            except Exception as e:
                print(f"Error loading {file}: {e}")
    
    def create(self, content: str, tags: List[str] = None, source: str = 'inferred') -> Memory:
        """Create new memory"""
        memory = Memory(
            id=f"mem_{datetime.now().timestamp()}",
            content=content,
            tags=tags or [],
            source=source
        )
        self.memories[memory.id] = memory
        self._save(memory)
        return memory
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID"""
        return self.memories.get(memory_id)
    
    def save(self, memory: Memory):
        """Save memory to storage"""
        self.memories[memory.id] = memory
        self._save(memory)
    
    def _save(self, memory: Memory):
        """Persist memory to file"""
        file_path = self.storage_path / f"{memory.id}.json"
        with open(file_path, 'w') as f:
            json.dump(memory.to_dict(), f, indent=2)
    
    def mark_as_critical(self, memory_id: str) -> Memory:
        """Mark memory as critical rule"""
        memory = self.get(memory_id)
        if memory:
            memory.mark_critical()
            self.save(memory)
        return memory
    
    def get_critical_rules(self) -> List[Memory]:
        """Get all critical rules"""
        return [m for m in self.memories.values() if m.is_critical]
    
    def all(self) -> List[Memory]:
        """Get all memories"""
        return list(self.memories.values())
    
    def migrate_to_v1_0_2(self) -> int:
        """Migrate all memories to v1.0.2 schema"""
        count = 0
        for memory in self.memories.values():
            # Ensure all new fields exist (backward compatibility)
            if not hasattr(memory, 'is_critical'):
                memory.is_critical = False
                memory.priority = 3
                memory.confidence = 0.5
                memory.source = 'inferred'
                memory.use_count = 0
                memory.success_count = 0
                memory.flagged_for_review = False
                self.save(memory)
                count += 1
        return count


# Example usage
if __name__ == '__main__':
    # Create memory system
    storage = Path('./memories')
    storage.mkdir(exist_ok=True)
    
    memory_system = MemorySystem(storage)
    
    # Create test memory
    memory = memory_system.create(
        content="Apache docs must be 100% English",
        tags=['rule', 'documentation'],
        source='user'
    )
    
    # Mark as critical
    memory_system.mark_as_critical(memory.id)
    
    # Get critical rules
    critical_rules = memory_system.get_critical_rules()
    print(f"Critical rules: {len(critical_rules)}")
    for rule in critical_rules:
        print(f"  - {rule.content} (confidence: {rule.confidence:.0%})")
    
    # Reinforce memory
    memory.reinforce(success=True)
    memory_system.save(memory)
    
    print(f"\n✅ Memory system v1.0.2 initialized successfully!")
