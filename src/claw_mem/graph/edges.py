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
Graph Edges - 概念介导图谱边类型

基于 GAAMA 论文的五边类型:
- NEXT: 情景序列 (Episode → Episode)
- DERIVED_FROM: 事实来源 (Fact → Episode)
- SYNTHESIZED_FROM: 反思来源 (Reflection → Episode/Fact)
- RELATED_TO: 相关关系 (任意节点间)
- HAS_CONCEPT: 概念关联 (任意节点 → Concept)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class EdgeType(Enum):
    """图谱边类型"""
    NEXT = "NEXT"                      # 情景序列
    DERIVED_FROM = "DERIVED_FROM"      # 事实来源
    SYNTHESIZED_FROM = "SYNTHESIZED_FROM"  # 反思来源
    RELATED_TO = "RELATED_TO"          # 相关关系
    HAS_CONCEPT = "HAS_CONCEPT"        # 概念关联

    def is_directed(self) -> bool:
        """是否是有向边"""
        return self != EdgeType.RELATED_TO


@dataclass
class Edge:
    """图谱边

    属性:
        source_id: 源节点 ID
        target_id: 目标节点 ID
        type: 边类型
        weight: 权重 (默认 1.0)
        metadata: 元数据
        created_at: 创建时间
    """
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type.value,
            'weight': self.weight,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """从字典创建"""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])

        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            type=EdgeType(data['type']),
            weight=data.get('weight', 1.0),
            metadata=data.get('metadata', {}),
            created_at=created_at,
        )


@dataclass
class NextEdge(Edge):
    """情景序列边 - Episode → Episode

    表示对话中连续的情景关系。
    """
    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.NEXT, **kwargs)


@dataclass
class DerivedFromEdge(Edge):
    """事实来源边 - Fact → Episode

    表示事实是从哪个情景中提取的。
    """
    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.DERIVED_FROM, **kwargs)


@dataclass
class SynthesizedFromEdge(Edge):
    """反思来源边 - Reflection → Episode/Fact

    表示反思是从哪些节点综合得出的。
    """
    source_node_ids: List[str] = field(default_factory=list)

    def __init__(self, source_id: str, target_id: str, source_node_ids: List[str] = None, **kwargs):
        super().__init__(source_id, target_id, EdgeType.SYNTHESIZED_FROM, **kwargs)
        self.source_node_ids = source_node_ids or []


@dataclass
class RelatedToEdge(Edge):
    """相关关系边 - 任意节点间

    表示两个节点之间的相关关系（无向边）。
    """
    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.RELATED_TO, **kwargs)


@dataclass
class HasConceptEdge(Edge):
    """概念关联边 - 任意节点 → Concept

    表示节点关联到某个概念。
    """
    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.HAS_CONCEPT, **kwargs)


def create_edge(
    edge_type: EdgeType,
    source_id: str,
    target_id: str,
    **kwargs
) -> Edge:
    """工厂函数：创建边

    Args:
        edge_type: 边类型
        source_id: 源节点 ID
        target_id: 目标节点 ID
        **kwargs: 其他参数

    Returns:
        Edge: 边实例

    Example:
        >>> edge = create_edge(EdgeType.NEXT, "ep_1", "ep_2")
    """
    if edge_type == EdgeType.NEXT:
        return NextEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.DERIVED_FROM:
        return DerivedFromEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.SYNTHESIZED_FROM:
        return SynthesizedFromEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.RELATED_TO:
        return RelatedToEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.HAS_CONCEPT:
        return HasConceptEdge(source_id, target_id, **kwargs)
    else:
        raise ValueError(f"Unknown edge type: {edge_type}")


__all__ = [
    'EdgeType',
    'Edge',
    'NextEdge',
    'DerivedFromEdge',
    'SynthesizedFromEdge',
    'RelatedToEdge',
    'HasConceptEdge',
    'create_edge',
]
