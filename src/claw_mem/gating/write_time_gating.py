"""
Write-Time Gating - 写时门控

来源: Selective Memory 论文
核心思想: 只存储显著信息，避免记忆冗余

References:
    - Selective Memory: Learning what to remember
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class GatingResult:
    """门控结果"""
    stored: bool
    tier: str  # 'active' | 'cold'
    salience_score: float
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class InMemoryStorage:
    """活跃记忆存储"""

    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def store(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """存储到活跃记忆"""
        stored_item = {
            **item,
            '_stored_at': datetime.now().isoformat(),
            '_tier': 'active'
        }
        self._items.append(stored_item)
        return stored_item

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取记忆项"""
        for item in self._items:
            if item.get('id') == key or item.get('content', '').startswith(key):
                return item
        return None

    def count(self) -> int:
        """返回存储数量"""
        return len(self._items)

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有记忆"""
        return self._items.copy()

    def clear(self):
        """清空存储"""
        self._items.clear()


class DiskStorage:
    """冷存储（磁盘）"""

    def __init__(self, storage_path: str = "/tmp/claw-mem-cold"):
        import os
        self._storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._count = 0

    def archive(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """归档到冷存储"""
        import json
        import os

        stored_item = {
            **item,
            '_stored_at': datetime.now().isoformat(),
            '_tier': 'cold'
        }

        # 使用时间戳作为文件名
        filename = f"{self._storage_path}/{int(time.time() * 1000)}.json"
        with open(filename, 'w') as f:
            json.dump(stored_item, f)

        self._count += 1
        return stored_item

    def count(self) -> int:
        """返回归档数量"""
        return self._count

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有归档"""
        import json
        import os

        items = []
        for filename in os.listdir(self._storage_path):
            if filename.endswith('.json'):
                with open(f"{self._storage_path}/{filename}") as f:
                    items.append(json.load(f))
        return items


class VersionChain:
    """版本链管理"""

    def __init__(self):
        self._chain: List[Dict[str, Any]] = []

    def append(self, item: Dict[str, Any]):
        """追加版本"""
        self._chain.append({
            **item,
            '_version': len(self._chain)
        })

    def get(self, index: int) -> Optional[Dict[str, Any]]:
        """获取指定版本"""
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def latest(self) -> Optional[Dict[str, Any]]:
        """获取最新版本"""
        return self._chain[-1] if self._chain else None

    def __len__(self) -> int:
        return len(self._chain)

    def clear(self):
        """清空版本链"""
        self._chain.clear()


class WriteTimeGating:
    """写时门控 - 只存储显著信息

    核心功能:
    1. 显著性评分 (salience scoring)
    2. 冷热存储分层 (hot/cold tiering)
    3. 版本链管理 (version chain)

    Example:
        >>> gating = WriteTimeGating(threshold=0.6)
        >>> result = gating.write({
        ...     'content': '重要决策...',
        ...     'source': 'user',
        ...     'context': {...}
        ... })
        >>> print(result.stored, result.tier)
        True 'active'
    """

    def __init__(
        self,
        threshold: float = 0.6,
        active_memory: Optional[Any] = None,
        cold_storage: Optional[Any] = None
    ):
        """
        Args:
            threshold: 显著性阈值，默认 0.6
            active_memory: 活跃记忆存储
            cold_storage: 冷存储
        """
        self.threshold = threshold
        self.active_memory = active_memory or InMemoryStorage()
        self.cold_storage = cold_storage or DiskStorage()
        self.salience_scorer = SalienceScorer()
        self.version_chain = VersionChain()

    def write(self, item: Dict[str, Any]) -> GatingResult:
        """写入记忆项

        Args:
            item: 记忆项，包含:
                - content: 内容
                - source: 来源 (user/agent/system)
                - context: 上下文
                - metadata: 元数据

        Returns:
            GatingResult: 门控结果
        """
        start_time = time.time()

        # 1. 计算显著性评分
        salience = self.salience_scorer.compute(item)

        # 2. 决定存储层级
        if salience >= self.threshold:
            # 高显著性 → 活跃记忆
            stored_item = self.active_memory.store(item)
            tier = 'active'
            stored = True
            reason = f"High salience ({salience:.2f} >= {self.threshold})"
        else:
            # 低显著性 → 冷存储
            stored_item = self.cold_storage.archive(item)
            tier = 'cold'
            stored = True
            reason = f"Low salience ({salience:.2f} < {self.threshold})"

        # 3. 更新版本链
        self.version_chain.append(stored_item)

        elapsed_ms = (time.time() - start_time) * 1000

        return GatingResult(
            stored=stored,
            tier=tier,
            salience_score=salience,
            reason=reason
        )

    def should_store(self, item: Dict[str, Any]) -> bool:
        """判断是否应该存储（预检查）

        Args:
            item: 记忆项

        Returns:
            bool: 是否应该存储到活跃记忆
        """
        salience = self.salience_scorer.compute(item)
        return salience >= self.threshold

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'active_count': self.active_memory.count(),
            'cold_count': self.cold_storage.count(),
            'version_chain_length': len(self.version_chain),
            'threshold': self.threshold
        }

    def promote(self, item_id: str, target_tier: str = 'active') -> bool:
        """提升记忆项到更高层级

        Args:
            item_id: 记忆项ID
            target_tier: 目标层级

        Returns:
            bool: 是否成功
        """
        # 从冷存储读取
        cold_items = self.cold_storage.list_all()
        for item in cold_items:
            if item.get('id') == item_id or item.get('content', '').startswith(item_id):
                # 移动到活跃记忆
                self.active_memory.store(item)
                return True
        return False


class SalienceScorer:
    """显著性评分器

    来源: Selective Memory 论文
    核心算法: 多维度加权评分

    评分维度:
    1. 来源声誉 (source reputation) - 权重 0.4
    2. 新颖性 (novelty) - 权重 0.3
    3. 可靠性 (reliability) - 权重 0.3
    """

    # 来源声誉权重
    SOURCE_REPUTATION = {
        'user': 1.0,      # 用户输入最高优先级
        'agent': 0.8,     # Agent 生成的信息
        'system': 0.6,    # 系统信息
        'external': 0.4   # 外部来源
    }

    def __init__(
        self,
        weights: Dict[str, float] = None,
        novelty_window: int = 100
    ):
        """
        Args:
            weights: 各维度权重，默认:
                - source_reputation: 0.4
                - novelty: 0.3
                - reliability: 0.3
            novelty_window: 新颖性计算窗口大小
        """
        self.weights = weights or {
            'source_reputation': 0.4,
            'novelty': 0.3,
            'reliability': 0.3
        }
        self.novelty_window = novelty_window
        self.recent_items: List[str] = []

    def compute(self, item: Dict[str, Any]) -> float:
        """计算显著性评分

        Args:
            item: 记忆项

        Returns:
            float: 显著性分数 (0.0 ~ 1.0)
        """
        # 1. 来源声誉 (40%)
        source_score = self._source_reputation(item.get('source', 'external'))

        # 2. 新颖性 (30%)
        novelty_score = self._novelty(item.get('content', ''))

        # 3. 可靠性 (30%)
        reliability_score = self._reliability(item)

        # 加权平均
        salience = (
            self.weights['source_reputation'] * source_score +
            self.weights['novelty'] * novelty_score +
            self.weights['reliability'] * reliability_score
        )

        # 更新最近记录
        self._update_recent(item.get('content', ''))

        return salience

    def _source_reputation(self, source: str) -> float:
        """来源声誉评分"""
        return self.SOURCE_REPUTATION.get(source, 0.5)

    def _novelty(self, content: str) -> float:
        """新颖性评分

        基于内容与最近记录的差异
        """
        if not self.recent_items:
            return 1.0  # 第一个项目最具新颖性

        # 简单实现：计算与最近内容的相似度
        # 实际实现可以使用更复杂的算法
        similarities = [
            self._simple_similarity(content, recent)
            for recent in self.recent_items
        ]

        avg_similarity = sum(similarities) / len(similarities)

        # 相似度越低，新颖性越高
        novelty = 1.0 - avg_similarity

        return max(0.0, min(1.0, novelty))

    def _reliability(self, item: Dict[str, Any]) -> float:
        """可靠性评分

        基于来源、验证状态、上下文完整性
        """
        score = 0.5  # 基础分

        # 来源加分
        source = item.get('source', '')
        if source in ['user', 'agent']:
            score += 0.2

        # 验证状态加分
        if item.get('verified', False):
            score += 0.2

        # 上下文完整性加分
        context = item.get('context', {})
        if context and len(context) > 0:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单相似度计算（基于词重叠）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _update_recent(self, content: str):
        """更新最近记录"""
        self.recent_items.append(content)

        # 保持窗口大小
        if len(self.recent_items) > self.novelty_window:
            self.recent_items.pop(0)
