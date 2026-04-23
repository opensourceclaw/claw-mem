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
Graph Nodes - 概念介导图谱节点类型

基于 GAAMA 论文的四节点类型:
- Episode: 对话片段、事件序列
- Fact: 提取的事实、知识
- Reflection: 总结、洞察、模式
- Concept: 抽象概念、主题
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import time


class NodeType(Enum):
    """图谱节点类型"""
    EPISODE = "episode"      # 情景
    FACT = "fact"            # 事实
    REFLECTION = "reflection"  # 反思
    CONCEPT = "concept"      # 概念


@dataclass
class Node:
    """图谱节点基类"""
    id: str
    type: NodeType
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """从字典创建"""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])

        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])

        node = cls(
            id=data['id'],
            type=NodeType(data['type']),
            content=data['content'],
            embedding=data.get('embedding'),
            metadata=data.get('metadata', {}),
            created_at=created_at,
            updated_at=updated_at,
        )
        return node


@dataclass
class EpisodeNode:
    """情景节点 - 对话片段、事件序列

    属性:
        sequence_id: 在对话中的序号
        speaker: 发言者 (user/agent/system)
        timestamp: 时间戳
        session_id: 会话 ID
    """
    id: str
    content: str
    sequence_id: int = 0
    speaker: Optional[str] = None
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @property
    def type(self) -> NodeType:
        return NodeType.EPISODE

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'sequence_id': self.sequence_id,
            'speaker': self.speaker,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EpisodeNode':
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        return cls(
            id=data['id'],
            content=data['content'],
            sequence_id=data.get('sequence_id', 0),
            speaker=data.get('speaker'),
            timestamp=timestamp,
            session_id=data.get('session_id'),
            embedding=data.get('embedding'),
            metadata=data.get('metadata', {}),
            created_at=created_at,
        )


@dataclass
class FactNode:
    """事实节点 - 提取的事实

    属性:
        confidence: 置信度 (0-1)
        source_episode: 来源情景 ID
        verified: 是否已验证
    """
    id: str
    content: str
    confidence: float = 1.0
    source_episode: Optional[str] = None
    verified: bool = False
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @property
    def type(self) -> NodeType:
        return NodeType.FACT

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'confidence': self.confidence,
            'source_episode': self.source_episode,
            'verified': self.verified,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FactNode':
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        return cls(
            id=data['id'],
            content=data['content'],
            confidence=data.get('confidence', 1.0),
            source_episode=data.get('source_episode'),
            verified=data.get('verified', False),
            embedding=data.get('embedding'),
            metadata=data.get('metadata', {}),
            created_at=created_at,
        )


@dataclass
class ReflectionNode:
    """反思节点 - 总结、洞察、模式

    属性:
        summary_type: 反思类型 (general/pattern/insight)
        source_node_ids: 来源节点 ID 列表
        importance: 重要性分数 (0-1)
    """
    id: str
    content: str
    summary_type: str = "general"
    source_node_ids: List[str] = field(default_factory=list)
    importance: float = 0.5
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @property
    def type(self) -> NodeType:
        return NodeType.REFLECTION

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'summary_type': self.summary_type,
            'source_node_ids': self.source_node_ids,
            'importance': self.importance,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReflectionNode':
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        return cls(
            id=data['id'],
            content=data['content'],
            summary_type=data.get('summary_type', 'general'),
            source_node_ids=data.get('source_node_ids', []),
            importance=data.get('importance', 0.5),
            embedding=data.get('embedding'),
            metadata=data.get('metadata', {}),
            created_at=created_at,
        )


@dataclass
class ConceptNode:
    """概念节点 - 抽象概念、主题

    属性:
        category: 概念类别 (general/topic/entity/action)
        frequency: 出现频率
        aliases: 别名列表
    """
    id: str
    content: str
    category: str = "general"
    frequency: int = 1
    aliases: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    @property
    def type(self) -> NodeType:
        return NodeType.CONCEPT

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'category': self.category,
            'frequency': self.frequency,
            'aliases': self.aliases,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConceptNode':
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        return cls(
            id=data['id'],
            content=data['content'],
            category=data.get('category', 'general'),
            frequency=data.get('frequency', 1),
            aliases=data.get('aliases', []),
            embedding=data.get('embedding'),
            metadata=data.get('metadata', {}),
            created_at=created_at,
        )


def create_node(node_type: NodeType, content: str, **kwargs) -> Any:
    """工厂函数：创建节点

    Args:
        node_type: 节点类型
        content: 内容
        **kwargs: 其他参数

    Returns:
        节点实例

    Example:
        >>> node = create_node(NodeType.EPISODE, "用户说：你好", speaker="user")
    """
    node_id = kwargs.pop('id', f"{node_type.value}_{int(time.time() * 1000000)}")

    if node_type == NodeType.EPISODE:
        return EpisodeNode(id=node_id, content=content, **kwargs)
    elif node_type == NodeType.FACT:
        return FactNode(id=node_id, content=content, **kwargs)
    elif node_type == NodeType.REFLECTION:
        return ReflectionNode(id=node_id, content=content, **kwargs)
    elif node_type == NodeType.CONCEPT:
        return ConceptNode(id=node_id, content=content, **kwargs)
    else:
        raise ValueError(f"Unknown node type: {node_type}")


__all__ = [
    'NodeType',
    'Node',
    'EpisodeNode',
    'FactNode',
    'ReflectionNode',
    'ConceptNode',
    'create_node',
]
