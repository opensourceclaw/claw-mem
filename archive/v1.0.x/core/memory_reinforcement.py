"""
Memory Reinforcement System v1.0.2

Reinforces memories through repeated use and corrections,
with confidence scoring and review queue management.

License: Apache-2.0
Documentation Language: 100% English (Apache Standard)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import sys

# Import memory system
sys.path.insert(0, str(Path(__file__).parent / 'core'))
from memory_v1_0_2 import Memory, MemorySystem


@dataclass
class ReviewItem:
    """Item in review queue"""
    memory: Memory
    reason: str  # Why this memory needs review
    priority: int  # 1-5 (5=highest)
    flagged_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        return f"[Priority {self.priority}] {self.memory.content} ({self.reason})"


class MemoryReinforcement:
    """Memory reinforcement system"""
    
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system
        self.review_queue: List[ReviewItem] = []
        
        # Reinforcement parameters
        self.success_bonus = 0.05  # +5% per success
        self.failure_penalty = 0.20  # -20% per failure
        self.confidence_cap = 1.0  # Max 100%
        self.confidence_floor = 0.0  # Min 0%
        self.low_confidence_threshold = 0.6  # Below 60% needs review
    
    def reinforce(self, memory_id: str, success: bool, context: str = "") -> Memory:
        """
        Reinforce a memory based on outcome
        
        Args:
            memory_id: Memory ID
            success: Whether the memory was used successfully
            context: Optional context about the reinforcement
        
        Returns:
            Updated memory
        """
        memory = self.memory_system.get(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
        
        # Update usage tracking
        memory.use_count += 1
        
        if success:
            memory.success_count += 1
            memory.confidence = min(
                self.confidence_cap,
                memory.confidence + self.success_bonus
            )
        else:
            memory.confidence = max(
                self.confidence_floor,
                memory.confidence - self.failure_penalty
            )
            memory.flagged_for_review = True
            
            # Add to review queue
            self._add_to_review_queue(
                memory,
                f"Failed validation (context: {context})",
                priority=4
            )
        
        memory.reinforced_at = datetime.now()
        
        # Check if confidence dropped below threshold
        if memory.confidence < self.low_confidence_threshold:
            self._add_to_review_queue(
                memory,
                f"Low confidence ({memory.confidence:.0%})",
                priority=3
            )
        
        # Save updated memory
        self.memory_system.save(memory)
        
        return memory
    
    def _add_to_review_queue(self, memory: Memory, reason: str, priority: int = 3):
        """Add memory to review queue"""
        # Check if already in queue
        for item in self.review_queue:
            if item.memory.id == memory.id:
                # Update existing item
                item.reason = reason
                item.priority = max(item.priority, priority)
                return
        
        # Add new item
        self.review_queue.append(ReviewItem(
            memory=memory,
            reason=reason,
            priority=priority
        ))
    
    def get_review_queue(self, limit: int = None) -> List[ReviewItem]:
        """Get review queue, sorted by priority"""
        sorted_queue = sorted(
            self.review_queue,
            key=lambda x: (x.priority, x.flagged_at),
            reverse=True
        )
        
        if limit:
            return sorted_queue[:limit]
        return sorted_queue
    
    def process_review(self, memory_id: str, corrected_content: str = None, keep: bool = True):
        """
        Process a review item
        
        Args:
            memory_id: Memory ID
            corrected_content: Optional corrected content
            keep: Whether to keep the memory (True) or delete (False)
        """
        memory = self.memory_system.get(memory_id)
        if not memory:
            return
        
        if corrected_content:
            memory.content = corrected_content
            memory.confidence = 0.8  # Reset confidence after correction
        
        if not keep:
            # Delete memory
            del self.memory_system.memories[memory_id]
        else:
            # Save updated memory
            memory.flagged_for_review = False
            self.memory_system.save(memory)
        
        # Remove from review queue
        self.review_queue = [
            item for item in self.review_queue 
            if item.memory.id != memory_id
        ]
    
    def get_daily_review_summary(self) -> Dict:
        """Get daily review summary"""
        today = datetime.now().date()
        
        # Count reviews by priority
        by_priority = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for item in self.review_queue:
            if item.flagged_at.date() == today:
                by_priority[item.priority] = by_priority.get(item.priority, 0) + 1
        
        # Count low confidence memories
        low_confidence = [
            m for m in self.memory_system.all()
            if m.confidence < self.low_confidence_threshold
        ]
        
        return {
            'date': today.isoformat(),
            'total_reviews': len(self.review_queue),
            'by_priority': by_priority,
            'low_confidence_memories': len(low_confidence),
            'total_memories': len(self.memory_system.all()),
            'average_confidence': sum(m.confidence for m in self.memory_system.all()) / len(self.memory_system.all()) if self.memory_system.all() else 0
        }
    
    def auto_cleanup(self, days_old: int = 30, min_confidence: float = 0.2):
        """
        Auto-cleanup old, low-confidence memories
        
        Args:
            days_old: Remove memories older than this
            min_confidence: Remove memories with confidence below this
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed = 0
        
        for memory in list(self.memory_system.all()):
            if (memory.created_at < cutoff_date and 
                memory.confidence < min_confidence and
                not memory.is_critical):
                
                # Don't delete critical rules
                del self.memory_system.memories[memory.id]
                removed += 1
        
        return removed


# Example usage
if __name__ == '__main__':
    # Create memory system
    storage = Path('./memories')
    storage.mkdir(exist_ok=True)
    
    memory_system = MemorySystem(storage)
    reinforcement = MemoryReinforcement(memory_system)
    
    # Create test memory
    memory = memory_system.create(
        content="Apache docs must be 100% English",
        tags=['rule', 'documentation'],
        source='user'
    )
    memory_system.mark_as_critical(memory.id)
    
    print("="*60)
    print("MEMORY REINFORCEMENT DEMO")
    print("="*60)
    
    # Test 1: Successful use
    print("\n1. Successful use (confidence should increase):")
    print(f"   Before: {memory.confidence:.0%}")
    reinforcement.reinforce(memory.id, success=True, context="Used in release")
    print(f"   After:  {memory.confidence:.0%}")
    
    # Test 2: Failed use
    print("\n2. Failed use (confidence should decrease):")
    print(f"   Before: {memory.confidence:.0%}")
    reinforcement.reinforce(memory.id, success=False, context="User corrected")
    print(f"   After:  {memory.confidence:.0%}")
    
    # Test 3: Review queue
    print("\n3. Review queue:")
    queue = reinforcement.get_review_queue()
    print(f"   Items in queue: {len(queue)}")
    for item in queue:
        print(f"   - {item}")
    
    # Test 4: Daily summary
    print("\n4. Daily review summary:")
    summary = reinforcement.get_daily_review_summary()
    print(f"   Total reviews: {summary['total_reviews']}")
    print(f"   Low confidence: {summary['low_confidence_memories']}")
    print(f"   Average confidence: {summary['average_confidence']:.0%}")
    
    print("\n" + "="*60)
    print("✅ Memory reinforcement system v1.0.2 initialized!")
    print("="*60)
