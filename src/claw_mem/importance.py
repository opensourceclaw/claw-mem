#!/usr/bin/env python3
"""
claw-mem Memory Importance Scoring

Ranks memories by importance for smarter retrieval and context injection.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass


@dataclass
class MemoryImportance:
    """记忆重要性数据结构"""
    base_score: float = 1.0
    type_weight: float = 0.0
    frequency_weight: float = 0.0
    recency_weight: float = 0.0
    total_score: float = 1.0
    
    def calculate_total(self) -> float:
        """计算总分"""
        self.total_score = min(2.0, self.base_score + self.type_weight + self.frequency_weight + self.recency_weight)
        return self.total_score


class ImportanceScorer:
    """
    记忆重要性评分器
    
    评分公式：
    Importance = Base(1.0) + Type Weight + Frequency Weight + Recency Weight
    
    上限：2.0
    """
    
    # 类型权重配置
    TYPE_WEIGHTS = {
        'semantic': 0.5,    # 核心事实：高权重
        'procedural': 0.3,  # 技能流程：中权重
        'episodic': 0.0,    # 情景记忆：低权重（会过期）
    }
    
    # 频率权重配置
    FREQUENCY_THRESHOLDS = [
        (10, 0.3),  # 访问 >10 次：+0.3
        (5, 0.2),   # 访问 >5 次：+0.2
        (1, 0.1),   # 访问 >1 次：+0.1
    ]
    
    # 新近度权重配置
    RECENCY_THRESHOLDS = [
        (7, 0.2),   # 7 天内访问：+0.2
        (30, 0.1),  # 30 天内访问：+0.1
    ]
    
    # 最大分数
    MAX_SCORE = 2.0
    
    def calculate(self, memory: dict) -> MemoryImportance:
        """
        计算记忆重要性分数
        
        Args:
            memory: 记忆字典，包含以下字段：
                - memory_type: 记忆类型 ('semantic'/'procedural'/'episodic')
                - access_count: 访问次数
                - accessed_at: 最后访问时间 (datetime)
        
        Returns:
            MemoryImportance: 重要性评分详情
        """
        importance = MemoryImportance()
        
        # 1. 类型权重
        memory_type = memory.get('memory_type', 'episodic')
        importance.type_weight = self.TYPE_WEIGHTS.get(memory_type, 0.0)
        
        # 2. 频率权重
        access_count = memory.get('access_count', 0)
        importance.frequency_weight = self._calculate_frequency_weight(access_count)
        
        # 3. 新近度权重
        accessed_at = memory.get('accessed_at')
        if accessed_at:
            if isinstance(accessed_at, str):
                accessed_at = datetime.fromisoformat(accessed_at)
            days_since_access = (datetime.now() - accessed_at).days
            importance.recency_weight = self._calculate_recency_weight(days_since_access)
        
        # 4. 计算总分
        importance.calculate_total()
        
        return importance
    
    def _calculate_frequency_weight(self, access_count: int) -> float:
        """计算频率权重"""
        for threshold, weight in self.FREQUENCY_THRESHOLDS:
            if access_count > threshold:
                return weight
        return 0.0
    
    def _calculate_recency_weight(self, days: int) -> float:
        """计算新近度权重"""
        for threshold, weight in self.RECENCY_THRESHOLDS:
            if days < threshold:
                return weight
        return 0.0
    
    def should_prioritize(self, memory: dict, threshold: float = 1.5) -> bool:
        """
        判断是否应该优先检索
        
        Args:
            memory: 记忆字典
            threshold: 优先级阈值（默认 1.5）
        
        Returns:
            bool: 是否应该优先
        """
        importance = self.calculate(memory)
        return importance.total_score >= threshold
    
    def should_archive(self, memory: dict, threshold: float = 0.3) -> bool:
        """
        判断是否应该归档（低优先级记忆）
        
        Args:
            memory: 记忆字典
            threshold: 归档阈值（默认 0.3）
        
        Returns:
            bool: 是否应该归档
        """
        importance = self.calculate(memory)
        
        # 只有情景记忆会过期
        if memory.get('memory_type') == 'episodic':
            return importance.total_score < threshold
        
        return False
    
    def rank_memories(self, memories: list) -> list:
        """
        对记忆列表按重要性排序
        
        Args:
            memories: 记忆列表
        
        Returns:
            list: 排序后的记忆列表（重要性从高到低）
        """
        scored_memories = []
        
        for memory in memories:
            importance = self.calculate(memory)
            scored_memories.append({
                'memory': memory,
                'importance': importance,
                'score': importance.total_score
            })
        
        # 按分数降序排序
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回排序后的记忆
        return [item['memory'] for item in scored_memories]
    
    def filter_high_priority(self, memories: list, threshold: float = 1.5, limit: Optional[int] = None) -> list:
        """
        筛选高优先级记忆
        
        Args:
            memories: 记忆列表
            threshold: 优先级阈值
            limit: 最大返回数量
        
        Returns:
            list: 高优先级记忆列表
        """
        high_priority = []
        
        for memory in memories:
            if self.should_prioritize(memory, threshold):
                high_priority.append(memory)
        
        # 按重要性排序
        high_priority = self.rank_memories(high_priority)
        
        # 限制数量
        if limit:
            high_priority = high_priority[:limit]
        
        return high_priority
    
    def get_importance_label(self, score: float) -> str:
        """
        获取重要性标签
        
        Args:
            score: 重要性分数
        
        Returns:
            str: 标签（高/中/低）
        """
        if score >= 1.7:
            return "高"
        elif score >= 1.3:
            return "中"
        else:
            return "低"
    
    def explain_score(self, memory: dict) -> str:
        """
        解释重要性评分原因
        
        Args:
            memory: 记忆字典
        
        Returns:
            str: 评分解释
        """
        importance = self.calculate(memory)
        
        explanation = f"重要性评分：{importance.total_score:.2f}/2.00\n"
        explanation += f"  - 基础分：{importance.base_score:.1f}\n"
        explanation += f"  - 类型权重：{importance.type_weight:.1f} ({memory.get('memory_type', 'unknown')})\n"
        explanation += f"  - 频率权重：{importance.frequency_weight:.1f} (访问{memory.get('access_count', 0)}次)\n"
        
        accessed_at = memory.get('accessed_at')
        if accessed_at:
            if isinstance(accessed_at, str):
                accessed_at = datetime.fromisoformat(accessed_at)
            days = (datetime.now() - accessed_at).days
            explanation += f"  - 新近度权重：{importance.recency_weight:.1f} ({days}天前访问)\n"
        
        explanation += f"\n优先级：{self.get_importance_label(importance.total_score)}"
        
        return explanation


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    scorer = ImportanceScorer()
    
    # 示例 1：高优先级记忆（语义 + 高频 + 新近）
    high_priority_memory = {
        'memory_type': 'semantic',
        'access_count': 15,
        'accessed_at': datetime.now() - timedelta(days=2),
        'content': '用户偏好使用中文'
    }
    
    importance = scorer.calculate(high_priority_memory)
    print(f"高优先级记忆评分：{importance.total_score:.2f}")
    print(scorer.explain_score(high_priority_memory))
    print()
    
    # 示例 2：低优先级记忆（情景 + 低频 + 陈旧）
    low_priority_memory = {
        'memory_type': 'episodic',
        'access_count': 1,
        'accessed_at': datetime.now() - timedelta(days=60),
        'content': '用户今天询问了天气'
    }
    
    importance = scorer.calculate(low_priority_memory)
    print(f"低优先级记忆评分：{importance.total_score:.2f}")
    print(scorer.explain_score(low_priority_memory))
    print()
    
    # 示例 3：记忆排序
    memories = [high_priority_memory, low_priority_memory]
    ranked = scorer.rank_memories(memories)
    
    print("排序结果:")
    for i, mem in enumerate(ranked, 1):
        importance = scorer.calculate(mem)
        print(f"{i}. [{scorer.get_importance_label(importance.total_score)}] {mem['content']}")
