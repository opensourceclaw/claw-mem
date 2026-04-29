"""
Write-Time Gating - 写时门控

来源: Selective Memory 论文
核心思想: 只storage显著信息,avoid记忆冗余

References:
    - Selective Memory: Learning what to remember
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time
import math


@dataclass
class GatingResult:
    """门控结果"""
    stored: bool
    tier: str  # 'active' | 'cold'
    salience_score: float
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GatingFilterResult:
    """门控过滤器结果"""
    should_store: bool
    importance_score: float
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class GatingFilter:
    """门控过滤器 - 基于重要性评分决定是否存储

    使用 ImportanceScorer 计算记忆重要性,
    根据阈值决定是否存储到主存储.

    Example:
        >>> from claw_mem.gating import GatingFilter
        >>> from claw_mem.importance import ImportanceScorer
        >>>
        >>> scorer = ImportanceScorer()
        >>> filter = GatingFilter(scorer=scorer, threshold=1.0)
        >>>
        >>> result = filter.should_store({
        ...     'memory_type': 'semantic',
        ...     'access_count': 5,
        ...     'content': '重要事实'
        ... })
        >>>
        >>> print(result.should_store)  # True/False
    """

    DEFAULT_THRESHOLD = 1.0  # 默认阈值

    # 内存类型默认权重
    TYPE_WEIGHTS = {
        'semantic': 0.5,
        'procedural': 0.3,
        'episodic': 0.0,
    }

    def __init__(
        self,
        scorer: Optional[Any] = None,
        threshold: float = DEFAULT_THRESHOLD,
        custom_score_func: Optional[Callable[[Dict], float]] = None
    ):
        """
        Args:
            scorer: 重要性评分器 (ImportanceScorer)
            threshold: 存储阈值 (默认 1.0)
            custom_score_func: 自定义评分函数
        """
        self.scorer = scorer
        self.threshold = threshold
        self.custom_score_func = custom_score_func

        # 如果没有提供scorer,使用内置评分
        if self.scorer is None and self.custom_score_func is None:
            self.scorer = _DefaultImportanceScorer()

    def should_store(self, memory: Dict[str, Any]) -> GatingFilterResult:
        """判断是否应该存储

        Args:
            memory: 记忆字典,包含:
                - memory_type: 记忆类型 (semantic/procedural/episodic)
                - access_count: 访问次数
                - accessed_at: 上次访问时间
                - content: 内容
                - source: 来源 (user/agent/system)

        Returns:
            GatingFilterResult: 门控结果
        """
        # 计算重要性评分
        if self.custom_score_func:
            score = self.custom_score_func(memory)
        elif self.scorer:
            score = self.scorer.calculate(memory).total_score
        else:
            # 默认评分
            score = self._default_score(memory)

        # 判断是否存储
        should_store = score >= self.threshold

        # 生成原因
        reason = self._generate_reason(memory, score, should_store)

        return GatingFilterResult(
            should_store=should_store,
            importance_score=score,
            reason=reason,
            metadata={
                'memory_type': memory.get('memory_type', 'unknown'),
                'threshold': self.threshold
            }
        )

    def _default_score(self, memory: Dict[str, Any]) -> float:
        """默认评分逻辑"""
        score = 1.0  # 基础分

        # 记忆类型权重
        mem_type = memory.get('memory_type', 'episodic')
        score += self.TYPE_WEIGHTS.get(mem_type, 0.0)

        # 访问频率权重
        access_count = memory.get('access_count', 0)
        if access_count > 10:
            score += 0.3
        elif access_count > 5:
            score += 0.2
        elif access_count > 1:
            score += 0.1

        # 来源权重
        source = memory.get('source', 'system')
        if source == 'user':
            score += 0.2
        elif source == 'agent':
            score += 0.1

        return min(2.0, score)

    def _generate_reason(self, memory: Dict[str, Any], score: float, should_store: bool) -> str:
        """生成决策原因"""
        mem_type = memory.get('memory_type', 'unknown')
        source = memory.get('source', 'unknown')

        if should_store:
            return f"High importance ({score:.2f} >= {self.threshold}): type={mem_type}, source={source}"
        else:
            return f"Low importance ({score:.2f} < {self.threshold}): type={mem_type}, source={source}"

    def set_threshold(self, threshold: float):
        """设置新阈值"""
        self.threshold = max(0.0, min(2.0, threshold))

    def get_threshold(self) -> float:
        """获取当前阈值"""
        return self.threshold


class _DefaultImportanceScorer:
    """默认重要性评分器"""

    def calculate(self, memory: Dict[str, Any]) -> 'MemoryImportance':
        """计算重要性"""
        # 简化实现
        score = 1.0
        mem_type = memory.get('memory_type') or 'episodic'

        type_weights = {'semantic': 0.5, 'procedural': 0.3, 'episodic': 0.0}
        score += type_weights.get(mem_type, 0.0)

        access_count = memory.get('access_count') or 0
        if access_count > 10:
            score += 0.3
        elif access_count > 5:
            score += 0.2
        elif access_count > 1:
            score += 0.1

        return MemoryImportance(total_score=min(2.0, score))


class MemoryImportance:
    """记忆重要性数据结构"""
    def __init__(self, total_score: float = 1.0):
        self.total_score = total_score


class AdaptiveThreshold:
    """自适应阈值 - 根据记忆数量动态调整

    当记忆数量较多时,提高阈值以过滤低重要性记忆;
    当记忆数量较少时,降低阈值以保留更多记忆.

    Example:
        >>> from claw_mem.gating import AdaptiveThreshold
        >>>
        >>> adapter = AdaptiveThreshold(
        ...     base_threshold=1.0,
        ...     min_threshold=0.5,
        ...     max_threshold=1.5,
        ...     memory_capacity=1000
        ... )
        >>>
        >>> # 根据当前记忆数量计算阈值
        >>> threshold = adapter.get_threshold(current_memory_count=500)
        >>> print(threshold)  # ~1.0
        >>>
        >>> threshold = adapter.get_threshold(current_memory_count=900)
        >>> print(threshold)  # ~1.3
    """

    def __init__(
        self,
        base_threshold: float = 1.0,
        min_threshold: float = 0.5,
        max_threshold: float = 1.5,
        memory_capacity: int = 1000,
        scale_factor: float = 0.5
    ):
        """
        Args:
            base_threshold: 基础阈值
            min_threshold: 最小阈值
            max_threshold: 最大阈值
            memory_capacity: 记忆容量参考值
            scale_factor: 缩放因子,控制阈值变化速度
        """
        self.base_threshold = base_threshold
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.memory_capacity = memory_capacity
        self.scale_factor = scale_factor

    def get_threshold(self, current_memory_count: int) -> float:
        """根据当前记忆数量计算阈值

        Args:
            current_memory_count: 当前记忆数量

        Returns:
            float: 动态计算的阈值
        """
        # 计算使用率
        usage_ratio = current_memory_count / self.memory_capacity

        # 使用 sigmoid 函数平滑过渡
        # 当 usage_ratio = 0.5 时,threshold = base_threshold
        # 当 usage_ratio 接近 0 时,threshold 接近 min_threshold
        # 当 usage_ratio 接近 1 时,threshold 接近 max_threshold

        # 调整偏移,使 base_threshold 在 usage_ratio=0.5 时
        adjusted = (usage_ratio - 0.5) * self.scale_factor * 2
        threshold = self.base_threshold + adjusted

        # 限制在 min/max 范围内
        return max(self.min_threshold, min(self.max_threshold, threshold))

    def get_stats(self, current_memory_count: int) -> Dict[str, Any]:
        """获取统计信息

        Args:
            current_memory_count: 当前记忆数量

        Returns:
            Dict: 统计信息
        """
        threshold = self.get_threshold(current_memory_count)
        return {
            'current_count': current_memory_count,
            'capacity': self.memory_capacity,
            'usage_ratio': current_memory_count / self.memory_capacity,
            'current_threshold': threshold,
            'base_threshold': self.base_threshold,
            'min_threshold': self.min_threshold,
            'max_threshold': self.max_threshold
        }

    def reset(self):
        """重置到基础阈值"""
        return self.base_threshold


class InMemoryStorage:
    """活跃记忆storage"""

    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def store(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """storage到活跃记忆"""
        stored_item = {
            **item,
            '_stored_at': datetime.now().isoformat(),
            '_tier': 'active'
        }
        self._items.append(stored_item)
        return stored_item

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """get记忆项"""
        for item in self._items:
            if item.get('id') == key or item.get('content', '').startswith(key):
                return item
        return None

    def count(self) -> int:
        """返回storage数量"""
        return len(self._items)

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有记忆"""
        return self._items.copy()

    def clear(self):
        """清空storage"""
        self._items.clear()


class DiskStorage:
    """冷storage(磁盘)"""

    def __init__(self, storage_path: str = "/tmp/claw-mem-cold"):
        import os
        self._storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._count = 0

    def archive(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """归档到冷storage"""
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
        """get指定版本"""
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def latest(self) -> Optional[Dict[str, Any]]:
        """get最新版本"""
        return self._chain[-1] if self._chain else None

    def __len__(self) -> int:
        return len(self._chain)

    def clear(self):
        """清空版本链"""
        self._chain.clear()


class WriteTimeGating:
    """写时门控 - 只storage显著信息

    核心功能:
    1. 显著性评分 (salience scoring)
    2. 冷热storage分层 (hot/cold tiering)
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
            threshold: 显著性阈值,默认 0.6
            active_memory: 活跃记忆storage
            cold_storage: 冷storage
        """
        self.threshold = threshold
        self.active_memory = active_memory or InMemoryStorage()
        self.cold_storage = cold_storage or DiskStorage()
        self.salience_scorer = SalienceScorer()
        self.version_chain = VersionChain()

    def write(self, item: Dict[str, Any]) -> GatingResult:
        """写入记忆项

        Args:
            item: 记忆项,包含:
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

        # 2. 决定storage层级
        if salience >= self.threshold:
            # 高显著性 → 活跃记忆
            stored_item = self.active_memory.store(item)
            tier = 'active'
            stored = True
            reason = f"High salience ({salience:.2f} >= {self.threshold})"
        else:
            # 低显著性 → 冷storage
            stored_item = self.cold_storage.archive(item)
            tier = 'cold'
            stored = True
            reason = f"Low salience ({salience:.2f} < {self.threshold})"

        # 3. update版本链
        self.version_chain.append(stored_item)

        elapsed_ms = (time.time() - start_time) * 1000

        return GatingResult(
            stored=stored,
            tier=tier,
            salience_score=salience,
            reason=reason
        )

    def should_store(self, item: Dict[str, Any]) -> bool:
        """判断是否shouldstorage(预check)

        Args:
            item: 记忆项

        Returns:
            bool: 是否shouldstorage到活跃记忆
        """
        salience = self.salience_scorer.compute(item)
        return salience >= self.threshold

    def get_stats(self) -> Dict[str, Any]:
        """get统计信息"""
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
        # 从冷storage读取
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
        'user': 1.0,      # user输入最高优first级
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
            weights: 各维度权重,默认:
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

        # update最近记录
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

        # 简单实现:计算与最近内容的相似度
        # 实际实现可以使用更复杂的算法
        similarities = [
            self._simple_similarity(content, recent)
            for recent in self.recent_items
        ]

        avg_similarity = sum(similarities) / len(similarities)

        # 相似度越低,新颖性越高
        novelty = 1.0 - avg_similarity

        return max(0.0, min(1.0, novelty))

    def _reliability(self, item: Dict[str, Any]) -> float:
        """可靠性评分

        基于来源,validate状态,上下文完整性
        """
        score = 0.5  # 基础分

        # 来源加分
        source = item.get('source', '')
        if source in ['user', 'agent']:
            score += 0.2

        # validate状态加分
        if item.get('verified', False):
            score += 0.2

        # 上下文完整性加分
        context = item.get('context', {})
        if context and len(context) > 0:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单相似度计算(基于词重叠)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _update_recent(self, content: str):
        """update最近记录"""
        self.recent_items.append(content)

        # 保持窗口大小
        if len(self.recent_items) > self.novelty_window:
            self.recent_items.pop(0)
