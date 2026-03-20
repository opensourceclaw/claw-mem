#!/usr/bin/env python3
"""
claw-mem Memory Decay Mechanism

Implements Ebbinghaus forgetting curve for automatic memory archival.
"""

import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


class MemoryDecay:
    """
    记忆衰减机制
    
    基于 Ebbinghaus 遗忘曲线，自动归档低优先级记忆
    """
    
    # 衰减常数（半衰期，单位：天）
    DECAY_CONSTANTS = {
        'episodic': 7,      # 情景记忆：7 天半衰期
        'semantic': 90,     # 语义记忆：90 天半衰期
        'procedural': 180,  # 程序记忆：180 天半衰期
    }
    
    # 归档阈值
    ARCHIVE_THRESHOLD = 0.3  # 激活水平低于此值则归档
    
    # 过期阈值（仅情景记忆）
    EXPIRY_DAYS = {
        'episodic': 30,     # 情景记忆 30 天后过期
        'semantic': None,   # 语义记忆永不过期
        'procedural': None, # 程序记忆永不过期
    }
    
    def __init__(self, workspace: str, custom_constants: Optional[Dict[str, float]] = None):
        """
        初始化记忆衰减
        
        Args:
            workspace: OpenClaw workspace 路径
            custom_constants: 自定义衰减常数（可选）
        """
        self.workspace = Path(workspace).expanduser()
        self.decay_constants = custom_constants or self.DECAY_CONSTANTS.copy()
        self.archive_log = self.workspace / ".claw-mem" / "decay_archive.log"
        self.archive_log.parent.mkdir(parents=True, exist_ok=True)
    
    def calculate_activation(self, memory: Dict) -> float:
        """
        计算记忆当前激活水平
        
        公式：A(t) = A₀ * exp(-t/τ)
        
        Args:
            memory: 记忆字典，包含：
                - memory_type: 记忆类型
                - accessed_at: 最后访问时间
                - activation_level: 当前激活水平
        
        Returns:
            float: 当前激活水平（0-1）
        """
        memory_type = memory.get('memory_type', 'episodic')
        accessed_at = memory.get('accessed_at')
        current_activation = memory.get('activation_level', 1.0)
        
        if not accessed_at:
            return current_activation
        
        # 解析时间
        if isinstance(accessed_at, str):
            accessed_at = datetime.fromisoformat(accessed_at)
        
        # 计算经过的天数
        days_since_access = (datetime.now() - accessed_at).days
        
        # 获取衰减常数
        tau = self.decay_constants.get(memory_type, 7)
        
        # Ebbinghaus 公式：A(t) = A₀ * exp(-t/τ)
        new_activation = current_activation * math.exp(-days_since_access / tau)
        
        # 如果今天访问过，提升激活水平
        if days_since_access == 0:
            new_activation = min(1.0, new_activation + 0.1)
        
        return max(0.0, new_activation)
    
    def should_archive(self, memory: Dict, threshold: Optional[float] = None) -> bool:
        """
        判断是否应该归档记忆
        
        Args:
            memory: 记忆字典
            threshold: 归档阈值（可选，默认 0.3）
        
        Returns:
            bool: 是否应该归档
        """
        if threshold is None:
            threshold = self.ARCHIVE_THRESHOLD
        
        memory_type = memory.get('memory_type', 'episodic')
        
        # 检查是否过期
        if self.is_expired(memory):
            return True
        
        # 检查激活水平
        activation = self.calculate_activation(memory)
        return activation < threshold
    
    def is_expired(self, memory: Dict) -> bool:
        """
        判断记忆是否过期
        
        Args:
            memory: 记忆字典
        
        Returns:
            bool: 是否过期
        """
        memory_type = memory.get('memory_type', 'episodic')
        accessed_at = memory.get('accessed_at')
        
        # 获取过期天数
        expiry_days = self.EXPIRY_DAYS.get(memory_type)
        
        # None 表示永不过期
        if expiry_days is None:
            return False
        
        if not accessed_at:
            return False
        
        # 解析时间
        if isinstance(accessed_at, str):
            accessed_at = datetime.fromisoformat(accessed_at)
        
        # 检查是否超过过期天数
        days_since_access = (datetime.now() - accessed_at).days
        return days_since_access > expiry_days
    
    def batch_decay(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        批量计算记忆衰减
        
        Args:
            memories: 记忆列表
        
        Returns:
            dict: 分类结果
                - active: 活跃记忆
                - low_priority: 低优先级记忆
                - expired: 过期记忆
        """
        result = {
            'active': [],
            'low_priority': [],
            'expired': [],
        }
        
        for memory in memories:
            if self.is_expired(memory):
                result['expired'].append(memory)
            elif self.should_archive(memory):
                result['low_priority'].append(memory)
            else:
                result['active'].append(memory)
        
        return result
    
    def archive_memories(self, memories: List[Dict], dry_run: bool = False) -> Dict:
        """
        归档记忆
        
        Args:
            memories: 要归档的记忆列表
            dry_run: 是否仅模拟（不实际归档）
        
        Returns:
            dict: 归档结果
        """
        result = {
            'total': len(memories),
            'archived': 0,
            'skipped': 0,
            'errors': [],
        }
        
        archive_dir = self.workspace / ".claw-mem" / "archived"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        for memory in memories:
            try:
                if not dry_run:
                    # 移动到归档目录
                    self._move_to_archive(memory, archive_dir)
                result['archived'] += 1
                self._log_archive(memory, dry_run)
            except Exception as e:
                result['errors'].append(str(e))
                result['skipped'] += 1
        
        return result
    
    def _move_to_archive(self, memory: Dict, archive_dir: Path):
        """移动记忆到归档目录"""
        # 简化实现：记录归档信息
        # 实际实现需要修改 MEMORY.md 文件
        pass
    
    def _log_archive(self, memory: Dict, dry_run: bool = False):
        """记录归档日志"""
        with open(self.archive_log, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            action = "DRY_RUN" if dry_run else "ARCHIVED"
            content = memory.get('content', '')[:50]
            f.write(f"[{timestamp}] {action}: {content}\n")
    
    def get_decay_statistics(self, memories: List[Dict]) -> Dict:
        """
        获取衰减统计信息
        
        Args:
            memories: 记忆列表
        
        Returns:
            dict: 统计信息
        """
        result = self.batch_decay(memories)
        
        stats = {
            'total': len(memories),
            'active': len(result['active']),
            'low_priority': len(result['low_priority']),
            'expired': len(result['expired']),
            'active_rate': len(result['active']) / len(memories) if memories else 0,
        }
        
        # 按类型统计
        by_type = {}
        for memory_type in ['episodic', 'semantic', 'procedural']:
            type_memories = [m for m in memories if m.get('memory_type') == memory_type]
            type_result = self.batch_decay(type_memories)
            by_type[memory_type] = {
                'total': len(type_memories),
                'active': len(type_result['active']),
                'expired': len(type_result['expired']),
            }
        
        stats['by_type'] = by_type
        
        return stats
    
    def update_activation(self, memory: Dict) -> float:
        """
        更新记忆激活水平（访问后）
        
        Args:
            memory: 记忆字典
        
        Returns:
            float: 新的激活水平
        """
        current_activation = self.calculate_activation(memory)
        
        # 访问后提升激活水平
        new_activation = min(1.0, current_activation + 0.2)
        
        # 更新访问时间
        memory['accessed_at'] = datetime.now().isoformat()
        memory['activation_level'] = new_activation
        
        return new_activation


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    workspace = "~/.openclaw/workspace"
    decay = MemoryDecay(workspace)
    
    print("测试 F102 记忆衰减机制\n")
    
    # 测试 1：计算激活水平
    print("测试 1: 计算激活水平")
    
    # 新近访问的记忆
    recent_memory = {
        'memory_type': 'episodic',
        'accessed_at': datetime.now() - timedelta(days=1),
        'activation_level': 1.0,
    }
    activation = decay.calculate_activation(recent_memory)
    print(f"  1 天前访问：{activation:.2f}")
    
    # 陈旧的记忆
    old_memory = {
        'memory_type': 'episodic',
        'accessed_at': datetime.now() - timedelta(days=60),
        'activation_level': 1.0,
    }
    activation = decay.calculate_activation(old_memory)
    print(f"  60 天前访问：{activation:.2f}")
    
    # 语义记忆（衰减慢）
    semantic_memory = {
        'memory_type': 'semantic',
        'accessed_at': datetime.now() - timedelta(days=60),
        'activation_level': 1.0,
    }
    activation = decay.calculate_activation(semantic_memory)
    print(f"  语义记忆（60 天）：{activation:.2f}")
    
    print()
    
    # 测试 2：是否应该归档
    print("测试 2: 归档判断")
    print(f"  新近记忆应归档：{decay.should_archive(recent_memory)}")
    print(f"  陈旧记忆应归档：{decay.should_archive(old_memory)}")
    print(f"  陈旧记忆已过期：{decay.is_expired(old_memory)}")
    
    print()
    
    # 测试 3：批量衰减
    print("测试 3: 批量衰减统计")
    test_memories = [
        {'memory_type': 'episodic', 'accessed_at': (datetime.now() - timedelta(days=1)).isoformat(), 'activation_level': 1.0},
        {'memory_type': 'episodic', 'accessed_at': (datetime.now() - timedelta(days=10)).isoformat(), 'activation_level': 1.0},
        {'memory_type': 'episodic', 'accessed_at': (datetime.now() - timedelta(days=60)).isoformat(), 'activation_level': 1.0},
        {'memory_type': 'semantic', 'accessed_at': (datetime.now() - timedelta(days=60)).isoformat(), 'activation_level': 1.0},
        {'memory_type': 'procedural', 'accessed_at': (datetime.now() - timedelta(days=100)).isoformat(), 'activation_level': 1.0},
    ]
    
    stats = decay.get_decay_statistics(test_memories)
    print(f"  总计：{stats['total']}")
    print(f"  活跃：{stats['active']} ({stats['active_rate']*100:.0f}%)")
    print(f"  低优先级：{stats['low_priority']}")
    print(f"  过期：{stats['expired']}")
