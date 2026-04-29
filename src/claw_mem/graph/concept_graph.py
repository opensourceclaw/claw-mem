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
Concept-Mediated Graph - 概念介导知识图谱

基于 GAAMA 论文实现的四节点五边图谱结构.

核心功能:
1. 添加对话(自动构建图谱)
2. 提取事实和概念
3. 生成反思
4. 混合检索
"""

from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
import uuid
import numpy as np

from .nodes import Node, NodeType, EpisodeNode, FactNode, ReflectionNode, ConceptNode
from .edges import Edge, EdgeType, create_edge
from .storage import GraphStorage, InMemoryGraphStorage
from .extractors import BaseExtractor, DummyExtractor


@dataclass
class RetrievalResult:
    """检索结果"""
    node: Node
    score: float
    type: str


class Embedder(Callable):
    """嵌入器接口"""

    def embed(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        raise NotImplementedError

    def __call__(self, text: str) -> List[float]:
        """使嵌入器可调用"""
        return self.embed(text)


class DummyEmbedder(Embedder):
    """虚拟嵌入器(用于测试)"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        """生成伪随机嵌入"""
        # 简单的哈希基础嵌入
        seed = hash(text) % (2 ** 32)
        np.random.seed(seed)
        vec = np.random.randn(self.dimension)
        vec = vec / np.linalg.norm(vec)  # 归一化
        return vec.tolist()


class LLMExtractor(Callable):
    """LLM 提取器接口"""

    def extract_facts(self, text: str) -> List[str]:
        """从文本提取事实"""
        raise NotImplementedError

    def extract_concepts(self, text: str) -> List[str]:
        """从文本提取概念"""
        raise NotImplementedError

    def generate_reflection(self, nodes: List[Node]) -> str:
        """从节点生成反思"""
        raise NotImplementedError


class ConceptMediatedGraph:
    """概念介导知识图谱

    Example:
        >>> graph = ConceptMediatedGraph()
        >>>
        >>> # 添加对话
        >>> graph.add_conversation([
        ...     {"speaker": "user", "content": "我想用 Python 做数据分析"},
        ...     {"speaker": "agent", "content": "推荐使用 pandas 库"}
        ... ])
        >>>
        >>> # 检索
        >>> results = graph.retrieve("数据分析工具")
    """

    def __init__(
        self,
        storage: Optional[GraphStorage] = None,
        embedder: Optional[Embedder] = None,
        extractor: Optional[BaseExtractor] = None,
    ):
        """
        Args:
            storage: 图谱storage后端
            embedder: 向量嵌入器
            extractor: 提取器(用于提取事实和概念)
        """
        self.storage = storage or InMemoryGraphStorage()
        self.embedder = embedder  # 允许 None,不自动创建 DummyEmbedder
        self.extractor = extractor or DummyExtractor()

    def add_conversation(
        self,
        turns: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> List[str]:
        """添加对话,自动构建图谱

        Args:
            turns: 对话轮次列表,每个包含:
                - speaker: 发言者
                - content: 内容
                - timestamp: 时间戳(可选)
            session_id: 会话 ID(可选)

        Returns:
            List[str]: 创建的 Episode 节点 ID 列表

        流程:
        1. 创建 Episode 节点
        2. 提取 Fact 节点(if有 LLM)
        3. 提取 Concept 节点(if有 LLM)
        4. 建立边关系
        """
        episode_ids = []
        session_id = session_id or str(uuid.uuid4())

        # Step 1: 创建 Episode 节点
        for i, turn in enumerate(turns):
            episode = EpisodeNode(
                id=self._generate_id(),
                content=turn['content'],
                sequence_id=i,
                speaker=turn.get('speaker', 'unknown'),
                timestamp=turn.get('timestamp'),
                session_id=session_id,
            )

            # 计算嵌入
            try:
                episode.embedding = self.embedder.embed(episode.content)
            except Exception:
                pass

            self.storage.save_node(episode)
            episode_ids.append(episode.id)

            # 建立 NEXT 边
            if i > 0:
                edge = create_edge(
                    EdgeType.NEXT,
                    episode_ids[i - 1],
                    episode.id
                )
                self.storage.save_edge(edge)

        # Step 2: 提取 Fact 节点
        if self.extractor:
            facts = self._extract_facts(turns)
            for fact_content in facts:
                fact = FactNode(
                    id=self._generate_id(),
                    content=fact_content,
                    source_episode=episode_ids[0] if episode_ids else None,
                    confidence=0.8,
                )

                try:
                    fact.embedding = self.embedder.embed(fact.content)
                except Exception:
                    pass

                self.storage.save_node(fact)

                # 建立 DERIVED_FROM 边
                for episode_id in episode_ids:
                    edge = create_edge(
                        EdgeType.DERIVED_FROM,
                        fact.id,
                        episode_id
                    )
                    self.storage.save_edge(edge)

        # Step 3: 提取 Concept 节点
        if self.extractor:
            concepts = self._extract_concepts(turns)
            for concept_content in concepts:
                # check是否已存在
                existing = self._find_concept(concept_content)
                if existing:
                    existing.frequency += 1
                    concept = existing
                else:
                    concept = ConceptNode(
                        id=self._generate_id(),
                        content=concept_content,
                    )

                    try:
                        concept.embedding = self.embedder.embed(concept.content)
                    except Exception:
                        pass

                    self.storage.save_node(concept)

                # 建立 HAS_CONCEPT 边
                for episode_id in episode_ids:
                    edge = create_edge(
                        EdgeType.HAS_CONCEPT,
                        episode_id,
                        concept.id
                    )
                    self.storage.save_edge(edge)

        return episode_ids

    def add_episode(
        self,
        content: str,
        speaker: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加单个情景

        Args:
            content: 内容
            speaker: 发言者
            metadata: 元数据

        Returns:
            str: 节点 ID
        """
        episode = EpisodeNode(
            id=self._generate_id(),
            content=content,
            speaker=speaker,
            metadata=metadata or {},
        )

        # 计算嵌入
        if self.embedder:
            try:
                episode.embedding = self.embedder.embed(episode.content)
            except Exception:
                pass

        self.storage.save_node(episode)
        return episode.id

    def add_fact(
        self,
        content: str,
        source_episode_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> str:
        """添加事实节点

        Args:
            content: 事实内容
            source_episode_id: 来源情景 ID
            confidence: 置信度

        Returns:
            str: 节点 ID
        """
        fact = FactNode(
            id=self._generate_id(),
            content=content,
            source_episode=source_episode_id,
            confidence=confidence,
        )

        try:
            fact.embedding = self.embedder.embed(fact.content)
        except Exception:
            pass

        self.storage.save_node(fact)

        # 建立来源边
        if source_episode_id:
            edge = create_edge(
                EdgeType.DERIVED_FROM,
                fact.id,
                source_episode_id
            )
            self.storage.save_edge(edge)

        return fact.id

    def add_concept(
        self,
        content: str,
        category: str = "general",
    ) -> str:
        """添加概念节点

        Args:
            content: 概念内容
            category: 概念类don't

        Returns:
            str: 节点 ID
        """
        # check是否已存在
        existing = self._find_concept(content)
        if existing:
            existing.frequency += 1
            return existing.id

        concept = ConceptNode(
            id=self._generate_id(),
            content=content,
            category=category,
        )

        try:
            concept.embedding = self.embedder.embed(concept.content)
        except Exception:
            pass

        self.storage.save_node(concept)
        return concept.id

    def add_reflection(
        self,
        content: str,
        source_node_ids: List[str],
        summary_type: str = "general",
    ) -> str:
        """添加反思节点

        Args:
            content: 反思内容
            source_node_ids: 来源节点 ID 列表
            summary_type: 反思类型

        Returns:
            str: 节点 ID
        """
        reflection = ReflectionNode(
            id=self._generate_id(),
            content=content,
            summary_type=summary_type,
            source_node_ids=source_node_ids,
        )

        try:
            reflection.embedding = self.embedder.embed(reflection.content)
        except Exception:
            pass

        self.storage.save_node(reflection)

        # 建立来源边
        for source_id in source_node_ids:
            edge = create_edge(
                EdgeType.SYNTHESIZED_FROM,
                reflection.id,
                source_id
            )
            self.storage.save_edge(edge)

        return reflection.id

    def retrieve(
        self,
        query: str,
        k: int = 10,
        alpha: float = 0.5,
        node_types: Optional[List[NodeType]] = None,
    ) -> List[RetrievalResult]:
        """混合检索

        Args:
            query: 查询文本
            k: 返回结果数量
            alpha: 语义检索权重 (0-1)
                - alpha=1: 纯语义检索
                - alpha=0: 纯 PPR
                - alpha=0.5: 混合
            node_types: 过滤节点类型(可选)

        Returns:
            List[RetrievalResult]: 检索结果
        """
        # 计算查询嵌入
        query_embedding = None
        if alpha > 0:
            try:
                query_embedding = self.embedder.embed(query)
            except Exception:
                pass

        # get所有节点
        all_nodes = self.storage.get_all_nodes()

        # 过滤节点类型
        if node_types:
            all_nodes = [n for n in all_nodes if n.type in node_types]

        # 语义检索
        semantic_scores: Dict[str, float] = {}
        if query_embedding:
            for node in all_nodes:
                if node.embedding:
                    score = self._cosine_similarity(query_embedding, node.embedding)
                    semantic_scores[node.id] = score

        # PPR 检索(简化版:基于节点度数)
        ppr_scores: Dict[str, float] = {}
        if alpha < 1:
            degree_dict = self._compute_ppr_scores(all_nodes)
            max_degree = max(degree_dict.values()) if degree_dict and any(degree_dict.values()) else 1
            if max_degree == 0:
                max_degree = 1
            for node_id, degree in degree_dict.items():
                ppr_scores[node_id] = degree / max_degree

        # 混合分数
        final_scores: Dict[str, float] = {}
        for node in all_nodes:
            semantic = semantic_scores.get(node.id, 0)
            ppr = ppr_scores.get(node.id, 0)
            final_scores[node.id] = alpha * semantic + (1 - alpha) * ppr

        # 排序返回
        sorted_nodes = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for node_id, score in sorted_nodes[:k]:
            node = self.storage.get_node(node_id)
            if node:
                results.append(RetrievalResult(
                    node=node,
                    score=score,
                    type=node.type.value,
                ))

        return results

    def get_node(self, node_id: str) -> Optional[Node]:
        """get节点"""
        return self.storage.get_node(node_id)

    def get_neighbors(self, node_id: str) -> List[Node]:
        """get邻居节点"""
        neighbor_ids = self.storage.get_neighbors(node_id)
        return [self.storage.get_node(nid) for nid in neighbor_ids if self.storage.get_node(nid)]

    def get_stats(self) -> Dict[str, Any]:
        """get统计信息"""
        if hasattr(self.storage, 'get_stats'):
            return self.storage.get_stats()
        return {
            'total_nodes': len(self.storage.get_all_nodes()),
            'total_edges': len(self.storage.get_all_edges()),
        }

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return str(uuid.uuid4())

    def _extract_facts(self, turns: List[Dict]) -> List[str]:
        """提取事实(使用 LLM)"""
        if not self.extractor:
            return []

        try:
            # 合并所有对话内容
            text = "\n".join([t['content'] for t in turns])
            return self.extractor.extract_facts(text)
        except Exception:
            return []

    def _extract_concepts(self, turns: List[Dict]) -> List[str]:
        """提取概念(使用 LLM)"""
        if not self.extractor:
            return []

        try:
            text = "\n".join([t['content'] for t in turns])
            return self.extractor.extract_concepts(text)
        except Exception:
            return []

    def _find_concept(self, content: str) -> Optional[ConceptNode]:
        """查找已存在的概念"""
        for node in self.storage.get_nodes_by_type(NodeType.CONCEPT):
            if isinstance(node, ConceptNode) and node.content == content:
                return node
        return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except Exception:
            return 0.0

    def _compute_ppr_scores(self, nodes: List[Node]) -> Dict[str, float]:
        """计算 PPR 分数(简化版:基于节点度数)"""
        scores = {}
        for node in nodes:
            neighbors = self.storage.get_neighbors(node.id)
            # 度数 + 概念节点权重加成
            score = len(neighbors)
            if node.type == NodeType.CONCEPT:
                if isinstance(node, ConceptNode):
                    score *= (1 + node.frequency * 0.1)
            scores[node.id] = score
        return scores


__all__ = [
    'ConceptMediatedGraph',
    'RetrievalResult',
    'Embedder',
    'DummyEmbedder',
    'LLMExtractor',
]
