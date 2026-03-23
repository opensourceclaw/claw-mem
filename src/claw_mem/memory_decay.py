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
claw-mem Memory Decay Mechanism

Implements Ebbinghaus forgetting curve for automatic memory archival.
Apache 2.0 License - Professional Open Source Style
"""

import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class MemoryDecay:
    """
    Memory decay mechanism
    
    Automatically archives low-priority memories based on Ebbinghaus forgetting curve
    """
    
    # Decay constants (half-life in days)
    DECAY_CONSTANTS = {
        'episodic': 7,      # Episodic memory: 7 days half-life
        'semantic': 90,     # Semantic memory: 90 days half-life
        'procedural': 180,  # Procedural memory: 180 days half-life
    }
    
    # Archive threshold
    ARCHIVE_THRESHOLD = 0.3  # Archive if activation level below this value
    
    # Expiry days (episodic memory only)
    EXPIRY_DAYS = {
        'episodic': 30,     # Episodic memory expires after 30 days
        'semantic': None,   # Semantic memory never expires
        'procedural': None, # Procedural memory never expires
    }
    
    def __init__(self, workspace: str, custom_constants: Optional[Dict[str, float]] = None):
        """
        Initialize memory decay
        
        Args:
            workspace: OpenClaw workspace path
            custom_constants: Custom decay constants (optional)
        """
        self.workspace = Path(workspace).expanduser()
        self.decay_constants = custom_constants or self.DECAY_CONSTANTS.copy()
        self.archive_log = self.workspace / ".claw-mem" / "decay_archive.log"
        self.archive_log.parent.mkdir(parents=True, exist_ok=True)
    
    def calculate_activation(self, memory: Dict) -> float:
        """
        Calculate current activation level of a memory
        
        Formula: A(t) = A₀ * exp(-t/τ)
        
        Args:
            memory: Memory dictionary containing:
                - memory_type: Type of memory
                - accessed_at: Last access time
                - activation_level: Current activation level
        
        Returns:
            float: Current activation level (0-1)
        """
        memory_type = memory.get('memory_type', 'episodic')
        accessed_at = memory.get('accessed_at')
        current_activation = memory.get('activation_level', 1.0)
        
        if not accessed_at:
            return current_activation
        
        # Parse timestamp
        if isinstance(accessed_at, str):
            accessed_at = datetime.fromisoformat(accessed_at)
        
        # Calculate days since last access
        days_since_access = (datetime.now() - accessed_at).days
        
        # Get decay constant
        tau = self.decay_constants.get(memory_type, 7)
        
        # Calculate activation: A(t) = A₀ * exp(-t/τ)
        new_activation = current_activation * math.exp(-days_since_access / tau)
        
        return max(0.0, min(1.0, new_activation))  # Clamp to [0, 1]
    
    def should_archive(self, memory: Dict) -> bool:
        """
        Determine if a memory should be archived
        
        Args:
            memory: Memory dictionary
        
        Returns:
            bool: True if memory should be archived
        """
        activation = self.calculate_activation(memory)
        return activation < self.ARCHIVE_THRESHOLD
    
    def should_expire(self, memory: Dict) -> bool:
        """
        Determine if a memory should be expired (deleted)
        
        Only applies to episodic memory
        
        Args:
            memory: Memory dictionary
        
        Returns:
            bool: True if memory should be expired
        """
        memory_type = memory.get('memory_type', 'episodic')
        accessed_at = memory.get('accessed_at')
        
        if not accessed_at or memory_type not in self.EXPIRY_DAYS:
            return False
        
        expiry_days = self.EXPIRY_DAYS[memory_type]
        if expiry_days is None:
            return False
        
        # Parse timestamp
        if isinstance(accessed_at, str):
            accessed_at = datetime.fromisoformat(accessed_at)
        
        # Check if expired
        days_since_access = (datetime.now() - accessed_at).days
        return days_since_access > expiry_days
    
    def process_memories(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Process a list of memories and categorize them
        
        Args:
            memories: List of memory dictionaries
        
        Returns:
            Dict with categories:
                - active: Memories to keep active
                - archive: Memories to archive
                - expire: Memories to delete
        """
        result = {
            'active': [],
            'archive': [],
            'expire': []
        }
        
        for memory in memories:
            if self.should_expire(memory):
                result['expire'].append(memory)
            elif self.should_archive(memory):
                result['archive'].append(memory)
            else:
                result['active'].append(memory)
        
        return result
    
    def log_archive(self, archived_memories: List[Dict]):
        """
        Log archived memories to file
        
        Args:
            archived_memories: List of archived memory dictionaries
        """
        if not archived_memories:
            return
        
        with open(self.archive_log, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n=== Archive Log: {timestamp} ===\n")
            f.write(f"Archived {len(archived_memories)} memories:\n")
            
            for memory in archived_memories:
                memory_id = memory.get('id', 'unknown')
                activation = memory.get('activation_level', 0)
                f.write(f"  - {memory_id} (activation: {activation:.3f})\n")


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    # Example usage
    decay = MemoryDecay(workspace="~/.openclaw/workspace")
    
    # Example memories
    memories = [
        {
            'id': 'mem_001',
            'memory_type': 'episodic',
            'accessed_at': datetime.now() - timedelta(days=10),
            'activation_level': 0.5
        },
        {
            'id': 'mem_002',
            'memory_type': 'semantic',
            'accessed_at': datetime.now() - timedelta(days=5),
            'activation_level': 0.8
        }
    ]
    
    # Process memories
    result = decay.process_memories(memories)
    
    print(f"Active: {len(result['active'])}")
    print(f"Archive: {len(result['archive'])}")
    print(f"Expire: {len(result['expire'])}")
