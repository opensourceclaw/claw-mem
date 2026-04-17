#!/usr/bin/env python3
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
claw-mem Memory Importance Scoring

Ranks memories by importance for smarter retrieval and context injection.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class MemoryImportance:
    """Memory importance data structure"""
    base_score: float = 1.0
    type_weight: float = 0.0
    frequency_weight: float = 0.0
    recency_weight: float = 0.0
    total_score: float = 1.0
    
    def calculate_total(self) -> float:
        """Calculate total score"""
        self.total_score = min(2.0, self.base_score + self.type_weight + self.frequency_weight + self.recency_weight)
        return self.total_score


class ImportanceScorer:
    """
    Memory importance scorer
    
    Scoring formula:
    Importance = Base(1.0) + Type Weight + Frequency Weight + Recency Weight
    
    Max: 2.0
    """
    
    # Class-based weight config
    TYPE_WEIGHTS = {
        'semantic': 0.5,    # Core facts: high weight
        'procedural': 0.3,  # Skills: medium weight
        'episodic': 0.0,    # Episodic: low weight (expires)
    }
    
    # Frequency weight config
    FREQUENCY_THRESHOLDS = [
        (10, 0.3),  # Access >10 times: +0.3
        (5, 0.2),   # Access >5 times: +0.2
        (1, 0.1),   # Access >1 time: +0.1
    ]
    
    # Recency weight config
    RECENCY_THRESHOLDS = [
        (7, 0.2),   # Access within 7 days: +0.2
        (30, 0.1),  # Access within 30 days: +0.1
    ]
    
    # Max score
    MAX_SCORE = 2.0
    
    def calculate(self, memory: dict) -> MemoryImportance:
        """
        Calculate memory importance score
        
        Args:
            memory: memory dict with fields:
                - memory_type: memory type ('semantic'/'procedural'/'episodic')
                - access_count: access count
                - accessed_at: last access time (datetime)
        
        Returns:
            MemoryImportance: importance score details
        """
        importance = MemoryImportance()
        
        # 1. Type weight
        memory_type = memory.get('memory_type', 'episodic')
        importance.type_weight = self.TYPE_WEIGHTS.get(memory_type, 0.0)
        
        # 2. Frequency weight
        access_count = memory.get('access_count', 0)
        importance.frequency_weight = self._calculate_frequency_weight(access_count)
        
        # 3. Recency weight
        accessed_at = memory.get('accessed_at')
        if accessed_at:
            if isinstance(accessed_at, str):
                accessed_at = datetime.fromisoformat(accessed_at)
            days_since_access = (datetime.now() - accessed_at).days
            importance.recency_weight = self._calculate_recency_weight(days_since_access)
        
        # 4. Calculate total
        importance.calculate_total()
        
        return importance
    
    def _calculate_frequency_weight(self, access_count: int) -> float:
        """Calculate frequency weight"""
        for threshold, weight in self.FREQUENCY_THRESHOLDS:
            if access_count > threshold:
                return weight
        return 0.0
    
    def _calculate_recency_weight(self, days: int) -> float:
        """Calculate recency weight"""
        for threshold, weight in self.RECENCY_THRESHOLDS:
            if days < threshold:
                return weight
        return 0.0
    
    def should_prioritize(self, memory: dict, threshold: float = 1.5) -> bool:
        """
        Check if memory should be prioritized for retrieval
        
        Args:
            memory: memory dict
            threshold: priority threshold (default 1.5)
        
        Returns:
            bool: whether to prioritize
        """
        importance = self.calculate(memory)
        return importance.total_score >= threshold
    
    def should_archive(self, memory: dict, threshold: float = 0.3) -> bool:
        """
        Check if memory should be archived (low priority)
        
        Args:
            memory: memory dict
            threshold: archive threshold (default 0.3)
        
        Returns:
            bool: whether to archive
        """
        importance = self.calculate(memory)
        
        # Only episodic memories expire
        if memory.get('memory_type') == 'episodic':
            return importance.total_score < threshold
        
        return False
    
    def rank_memories(self, memories: list) -> list:
        """
        Rank memories by importance
        
        Args:
            memories: memory list
        
        Returns:
            list: sorted memory list (highest importance first)
        """
        scored_memories = []
        
        for memory in memories:
            importance = self.calculate(memory)
            scored_memories.append({
                'memory': memory,
                'importance': importance,
                'score': importance.total_score
            })
        
        # Sort by score descending
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        
        # Return sorted memories
        return [item['memory'] for item in scored_memories]
    
    def filter_high_priority(self, memories: list, threshold: float = 1.5, limit: Optional[int] = None) -> list:
        """
        Filter high priority memories
        
        Args:
            memories: memory list
            threshold: priority threshold
            limit: max return count
        
        Returns:
            list: high priority memory list
        """
        high_priority = []
        
        for memory in memories:
            if self.should_prioritize(memory, threshold):
                high_priority.append(memory)
        
        # Sort by importance
        high_priority = self.rank_memories(high_priority)
        
        # Limit count
        if limit:
            high_priority = high_priority[:limit]
        
        return high_priority
    
    def get_importance_label(self, score: float) -> str:
        """
        Get importance label
        
        Args:
            score: importance score
        
        Returns:
            str: label (high/medium/low)
        """
        if score >= 1.7:
            return "high"
        elif score >= 1.3:
            return "medium"
        else:
            return "low"
    
    def explain_score(self, memory: dict) -> str:
        """
        Explain importance score breakdown
        
        Args:
            memory: memory dict
        
        Returns:
            str: score explanation
        """
        importance = self.calculate(memory)
        
        explanation = f"Importance score: {importance.total_score:.2f}/2.00\n"
        explanation += f"  - Base score: {importance.base_score:.1f}\n"
        explanation += f"  - Type weight: {importance.type_weight:.1f} ({memory.get('memory_type', 'unknown')})\n"
        explanation += f"  - Frequency weight: {importance.frequency_weight:.1f} ({memory.get('access_count', 0)} accesses)\n"
        
        accessed_at = memory.get('accessed_at')
        if accessed_at:
            if isinstance(accessed_at, str):
                accessed_at = datetime.fromisoformat(accessed_at)
            days = (datetime.now() - accessed_at).days
            explanation += f"  - Recency weight: {importance.recency_weight:.1f} ({days} days ago)\n"
        
        explanation += f"\nPriority: {self.get_importance_label(importance.total_score)}"
        
        return explanation


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    scorer = ImportanceScorer()
    
    # Example 1: High priority memory (semantic + high freq + recent)
    high_priority_memory = {
        'memory_type': 'semantic',
        'access_count': 15,
        'accessed_at': datetime.now() - timedelta(days=2),
        'content': 'User prefers Chinese language'
    }
    
    importance = scorer.calculate(high_priority_memory)
    print(f"High priority memory score: {importance.total_score:.2f}")
    print(scorer.explain_score(high_priority_memory))
    print()
    
    # Example 2: Low priority memory (episodic + low freq + old)
    low_priority_memory = {
        'memory_type': 'episodic',
        'access_count': 1,
        'accessed_at': datetime.now() - timedelta(days=60),
        'content': 'User asked about weather today'
    }
    
    importance = scorer.calculate(low_priority_memory)
    print(f"Low priority memory score: {importance.total_score:.2f}")
    print(scorer.explain_score(low_priority_memory))
    print()
    
    # Example 3: Memory ranking
    memories = [high_priority_memory, low_priority_memory]
    ranked = scorer.rank_memories(memories)
    
    print("Ranking results:")
    for i, mem in enumerate(ranked, 1):
        importance = scorer.calculate(mem)
        print(f"{i}. [{scorer.get_importance_label(importance.total_score)}] {mem['content']}")
