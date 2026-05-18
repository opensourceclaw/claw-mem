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
Concept-Mediated Graph - Concept-mediated knowledge graph

Based on GAAMA paper implementation of four-node five-edge graph structure.

Core features:
1. Add conversations (auto-build graph)
2. Extract facts and concepts
3. Generate reflections
4. Hybrid retrieval
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
    """Retrieval result"""

    node: Node
    score: float
    type: str


class Embedder(Callable):
    """Embedder interface"""

    def embed(self, text: str) -> List[float]:
        """Generate text embedding vector"""
        raise NotImplementedError

    def __call__(self, text: str) -> List[float]:
        """Make embedder callable"""
        return self.embed(text)


class DummyEmbedder(Embedder):
    """Dummy embedder (for testing)"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        """Generate pseudo-random embedding"""
        # Simple hash-based embedding
        seed = hash(text) % (2**32)
        np.random.seed(seed)
        vec = np.random.randn(self.dimension)
        vec = vec / np.linalg.norm(vec)  # Normalize
        return vec.tolist()


class LLMExtractor(Callable):
    """LLM extractor interface"""

    def extract_facts(self, text: str) -> List[str]:
        """Extract facts from text"""
        raise NotImplementedError

    def extract_concepts(self, text: str) -> List[str]:
        """Extract concepts from text"""
        raise NotImplementedError

    def generate_reflection(self, nodes: List[Node]) -> str:
        """Generate reflection from nodes"""
        raise NotImplementedError


class ConceptMediatedGraph:
    """Concept-mediated knowledge graph

    Example:
        >>> graph = ConceptMediatedGraph()
        >>>
        >>> # Add conversation
        >>> graph.add_conversation([
        ...     {"speaker": "user", "content": "I want to do data analysis with Python"},
        ...     {"speaker": "agent", "content": "I recommend using pandas library"}
        ... ])
        >>>
        >>> # Retrieve
        >>> results = graph.retrieve("data analysis tools")
    """

    def __init__(
        self,
        storage: Optional[GraphStorage] = None,
        embedder: Optional[Embedder] = None,
        extractor: Optional[BaseExtractor] = None,
    ):
        """
        Args:
            storage: Graph storage backend
            embedder: Vector embedder
            extractor: Extractor (for extracting facts and concepts)
        """
        self.storage = storage or InMemoryGraphStorage()
        self.embedder = embedder  # Allow None, do not auto-create DummyEmbedder
        self.extractor = extractor or DummyExtractor()

    def add_conversation(
        self, turns: List[Dict[str, Any]], session_id: Optional[str] = None
    ) -> List[str]:
        """Add conversation, auto-build graph

        Args:
            turns: List of conversation turns, each containing:
                - speaker: Speaker
                - content: Content
                - timestamp: Timestamp (optional)
            session_id: Session ID (optional)

        Returns:
            List[str]: List of created Episode node IDs

        Flow:
        1. Create Episode nodes
        2. Extract Fact nodes (if LLM available)
        3. Extract Concept nodes (if LLM available)
        4. Establish edge relationships
        """
        episode_ids = []
        session_id = session_id or str(uuid.uuid4())

        # Step 1: Create Episode nodes
        for i, turn in enumerate(turns):
            episode = EpisodeNode(
                id=self._generate_id(),
                content=turn["content"],
                sequence_id=i,
                speaker=turn.get("speaker", "unknown"),
                timestamp=turn.get("timestamp"),
                session_id=session_id,
            )

            # Compute embedding
            try:
                episode.embedding = self.embedder.embed(episode.content)
            except Exception:
                pass

            self.storage.save_node(episode)
            episode_ids.append(episode.id)

            # Create NEXT edge
            if i > 0:
                edge = create_edge(EdgeType.NEXT, episode_ids[i - 1], episode.id)
                self.storage.save_edge(edge)

        # Step 2: Extract Fact nodes
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

                # Create DERIVED_FROM edge
                for episode_id in episode_ids:
                    edge = create_edge(EdgeType.DERIVED_FROM, fact.id, episode_id)
                    self.storage.save_edge(edge)

        # Step 3: Extract Concept nodes
        if self.extractor:
            concepts = self._extract_concepts(turns)
            for concept_content in concepts:
                # Check if already exists
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

                # Create HAS_CONCEPT edge
                for episode_id in episode_ids:
                    edge = create_edge(EdgeType.HAS_CONCEPT, episode_id, concept.id)
                    self.storage.save_edge(edge)

        return episode_ids

    def add_episode(
        self, content: str, speaker: str = "unknown", metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a single episode

        Args:
            content: Content
            speaker: Speaker
            metadata: Metadata

        Returns:
            str: Node ID
        """
        episode = EpisodeNode(
            id=self._generate_id(),
            content=content,
            speaker=speaker,
            metadata=metadata or {},
        )

        # Compute embedding
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
        """Add fact node

        Args:
            content: Fact content
            source_episode_id: Source episode ID
            confidence: Confidence level

        Returns:
            str: Node ID
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

        # Create source edge
        if source_episode_id:
            edge = create_edge(EdgeType.DERIVED_FROM, fact.id, source_episode_id)
            self.storage.save_edge(edge)

        return fact.id

    def add_concept(
        self,
        content: str,
        category: str = "general",
    ) -> str:
        """Add concept node

        Args:
            content: Concept content
            category: Concept category

        Returns:
            str: Node ID
        """
        # Check if already exists
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
        """Add reflection node

        Args:
            content: Reflection content
            source_node_ids: List of source node IDs
            summary_type: Reflection type

        Returns:
            str: Node ID
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

        # Create source edges
        for source_id in source_node_ids:
            edge = create_edge(EdgeType.SYNTHESIZED_FROM, reflection.id, source_id)
            self.storage.save_edge(edge)

        return reflection.id

    def retrieve(
        self,
        query: str,
        k: int = 10,
        alpha: float = 0.5,
        node_types: Optional[List[NodeType]] = None,
    ) -> List[RetrievalResult]:
        """Hybrid retrieval

        Args:
            query: Query text
            k: Number of results to return
            alpha: Semantic retrieval weight (0-1)
                - alpha=1: Pure semantic retrieval
                - alpha=0: Pure PPR
                - alpha=0.5: Hybrid
            node_types: Filter by node types (optional)

        Returns:
            List[RetrievalResult]: Retrieval results
        """
        # Compute query embedding
        query_embedding = None
        if alpha > 0:
            try:
                query_embedding = self.embedder.embed(query)
            except Exception:
                pass

        # Get all nodes
        all_nodes = self.storage.get_all_nodes()

        # Filter by node type
        if node_types:
            all_nodes = [n for n in all_nodes if n.type in node_types]

        # Semantic retrieval
        semantic_scores: Dict[str, float] = {}
        if query_embedding:
            for node in all_nodes:
                if node.embedding:
                    score = self._cosine_similarity(query_embedding, node.embedding)
                    semantic_scores[node.id] = score

        # PPR retrieval (simplified: based on node degree)
        ppr_scores: Dict[str, float] = {}
        if alpha < 1:
            degree_dict = self._compute_ppr_scores(all_nodes)
            max_degree = (
                max(degree_dict.values()) if degree_dict and any(degree_dict.values()) else 1
            )
            if max_degree == 0:
                max_degree = 1
            for node_id, degree in degree_dict.items():
                ppr_scores[node_id] = degree / max_degree

        # Hybrid scores
        final_scores: Dict[str, float] = {}
        for node in all_nodes:
            semantic = semantic_scores.get(node.id, 0)
            ppr = ppr_scores.get(node.id, 0)
            final_scores[node.id] = alpha * semantic + (1 - alpha) * ppr

        # Sort and return
        sorted_nodes = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for node_id, score in sorted_nodes[:k]:
            node = self.storage.get_node(node_id)
            if node:
                results.append(
                    RetrievalResult(
                        node=node,
                        score=score,
                        type=node.type.value,
                    )
                )

        return results

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node"""
        return self.storage.get_node(node_id)

    def get_neighbors(self, node_id: str) -> List[Node]:
        """Get neighbor nodes"""
        neighbor_ids = self.storage.get_neighbors(node_id)
        return [self.storage.get_node(nid) for nid in neighbor_ids if self.storage.get_node(nid)]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        if hasattr(self.storage, "get_stats"):
            return self.storage.get_stats()
        return {
            "total_nodes": len(self.storage.get_all_nodes()),
            "total_edges": len(self.storage.get_all_edges()),
        }

    def _generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())

    def _extract_facts(self, turns: List[Dict]) -> List[str]:
        """Extract facts (using LLM)"""
        if not self.extractor:
            return []

        try:
            # Merge all conversation content
            text = "\n".join([t["content"] for t in turns])
            return self.extractor.extract_facts(text)
        except Exception:
            return []

    def _extract_concepts(self, turns: List[Dict]) -> List[str]:
        """Extract concepts (using LLM)"""
        if not self.extractor:
            return []

        try:
            text = "\n".join([t["content"] for t in turns])
            return self.extractor.extract_concepts(text)
        except Exception:
            return []

    def _find_concept(self, content: str) -> Optional[ConceptNode]:
        """Find existing concept"""
        for node in self.storage.get_nodes_by_type(NodeType.CONCEPT):
            if isinstance(node, ConceptNode) and node.content == content:
                return node
        return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except Exception:
            return 0.0

    def _compute_ppr_scores(self, nodes: List[Node]) -> Dict[str, float]:
        """Compute PPR scores (simplified: based on node degree)"""
        scores = {}
        for node in nodes:
            neighbors = self.storage.get_neighbors(node.id)
            # Degree + concept node weight bonus
            score = len(neighbors)
            if node.type == NodeType.CONCEPT:
                if isinstance(node, ConceptNode):
                    score *= 1 + node.frequency * 0.1
            scores[node.id] = score
        return scores


__all__ = [
    "ConceptMediatedGraph",
    "RetrievalResult",
    "Embedder",
    "DummyEmbedder",
    "LLMExtractor",
]
