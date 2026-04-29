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
Semantic Retriever for claw-mem v2.5.0
Embedding-based semantic search over memory
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np

from .embedding_service import get_embedding_service, EmbeddingService


class SemanticRetriever:
    """Semantic Retriever

    Features:
    - Embedding-based similarity search
    - Configurable top-k retrieval
    - Score threshold filtering
    - Integration with memory storage
    """

    def __init__(
        self,
        provider: str = "auto",
        model: str = "text-embedding-3-small",
        top_k: int = 10,
        score_threshold: float = 0.7
    ):
        """Initialize semantic retriever

        Args:
            provider: "openai", "local", or "auto"
            model: Embedding model name
            top_k: Number of results to return
            score_threshold: Minimum similarity score
        """
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.embedding_service = get_embedding_service(provider=provider, model=model)
        self.dimension = self.embedding_service.get_dimension()

        # Index storage: list of (id, text, embedding, metadata)
        self._index: List[Tuple[str, str, np.ndarray, Dict]] = []
        self._id_to_index: Dict[str, int] = {}

    def add(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add document to semantic index

        Args:
            id: Unique document ID
            text: Document text
            metadata: Additional metadata
        """
        embedding = self.embedding_service.encode_single(text)
        embedding_array = np.array(embedding)

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm

        idx = len(self._index)
        self._index.append((id, text, embedding_array, metadata or {}))
        self._id_to_index[id] = idx

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents

        Args:
            query: Search query
            top_k: Override default top_k
            score_threshold: Override default threshold
            filters: Filter by metadata

        Returns:
            List of results with id, text, score, metadata
        """
        if not self._index:
            return []

        # Encode query
        query_embedding = self.embedding_service.encode_single(query)
        query_array = np.array(query_embedding)

        # Normalize
        norm = np.linalg.norm(query_array)
        if norm > 0:
            query_array = query_array / norm

        # Calculate similarities
        results = []
        for id, text, embedding, metadata in self._index:
            # Apply filters
            if filters:
                match = all(
                    metadata.get(k) == v
                    for k, v in filters.items()
                )
                if not match:
                    continue

            # Cosine similarity
            score = float(np.dot(query_array, embedding))

            # Apply threshold
            threshold = score_threshold if score_threshold is not None else self.score_threshold
            if score >= threshold:
                results.append({
                    "id": id,
                    "text": text,
                    "score": score,
                    "metadata": metadata
                })

        # Sort by score and return top-k
        results.sort(key=lambda x: x["score"], reverse=True)
        k = top_k if top_k is not None else self.top_k
        return results[:k]

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID

        Args:
            id: Document ID

        Returns:
            Document or None
        """
        if id not in self._id_to_index:
            return None

        idx = self._id_to_index[id]
        doc_id, text, embedding, metadata = self._index[idx]
        return {
            "id": doc_id,
            "text": text,
            "metadata": metadata
        }

    def delete(self, id: str) -> bool:
        """Delete document by ID

        Args:
            id: Document ID

        Returns:
            True if deleted
        """
        if id not in self._id_to_index:
            return False

        idx = self._id_to_index[id]
        del self._index[idx]

        # Rebuild index
        self._rebuild_index()
        return True

    def _rebuild_index(self):
        """Rebuild ID to index mapping"""
        self._id_to_index = {
            doc_id: idx
            for idx, (doc_id, _, _, _) in enumerate(self._index)
        }

    def clear(self):
        """Clear all documents"""
        self._index.clear()
        self._id_to_index.clear()

    def count(self) -> int:
        """Get number of documents"""
        return len(self._index)

    def batch_add(
        self,
        documents: List[Dict[str, Any]]
    ):
        """Add multiple documents

        Args:
            documents: List of {id, text, metadata}
        """
        for doc in documents:
            self.add(
                id=doc["id"],
                text=doc["text"],
                metadata=doc.get("metadata")
            )


# Default instance
_semantic_retriever: Optional[SemanticRetriever] = None


def get_semantic_retriever(
    provider: str = "auto",
    model: str = "text-embedding-3-small",
    top_k: int = 10
) -> SemanticRetriever:
    """Get global semantic retriever instance"""
    global _semantic_retriever

    if _semantic_retriever is None:
        _semantic_retriever = SemanticRetriever(
            provider=provider,
            model=model,
            top_k=top_k
        )

    return _semantic_retriever
