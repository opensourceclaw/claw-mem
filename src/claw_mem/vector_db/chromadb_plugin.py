"""
ChromaDB Plugin for claw-mem vector database

Local-first, embedded vector database implementation
"""

from typing import List, Dict, Optional, Any
import os
from pathlib import Path

from .plugin import VectorDBPlugin, SearchResult, VectorDBType


class ChromaDBPlugin(VectorDBPlugin):
    """
    ChromaDB implementation of VectorDBPlugin

    Configuration:
        - path: Local storage path (default: ./vector_store)
        - collection_name: Name of the collection (default: memories)
        - embedding_model: Embedding model to use
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        self.path = config.get("path", "./vector_store")
        self.collection_name = config.get("collection_name", "memories")
        self.embedding_model = config.get("embedding_model", "all-MiniLM-L6-v2")

        self.client = None
        self.collection = None
        self._embedding_fn = None

    def connect(self) -> bool:
        """Initialize ChromaDB connection"""
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            # Create persistent client
            os.makedirs(self.path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.path)

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "claw-mem memories"}
            )

            # Load embedding model
            self._embedding_fn = SentenceTransformer(self.embedding_model)

            return True

        except ImportError:
            raise ImportError(
                "ChromaDB or sentence-transformers not installed. "
                "Install with: pip install chromadb sentence-transformers"
            )
        except Exception as e:
            print(f"ChromaDB connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Close ChromaDB connection"""
        self.client = None
        self.collection = None

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts"""
        if self._embedding_fn is None:
            self.connect()
        embeddings = self._embedding_fn.encode(texts)
        return embeddings.tolist()

    def add(
        self,
        documents: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Add documents to ChromaDB"""
        if self.collection is None:
            self.connect()

        embeddings = self._get_embeddings(documents)

        # Prepare metadata
        if metadata is None:
            metadata = [{} for _ in documents]

        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            ids=ids,
            metadatas=metadata
        )

        return True

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents"""
        if self.collection is None:
            self.connect()

        # Get query embedding
        query_embedding = self._get_embeddings([query])[0]

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )

        # Convert to standard format
        search_results = []
        if results and results.get("ids") and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                search_results.append(SearchResult(
                    id=doc_id,
                    content=results["documents"][0][i],
                    score=1.0 - (results.get("distances", [[0]])[0][i] or 0),  # Convert distance to similarity
                    metadata=results.get("metadatas", [{}])[0][i] if results.get("metadatas") else None
                ))

        return search_results

    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        if self.collection is None:
            return False

        self.collection.delete(ids=ids)
        return True

    def get(self, id: str) -> Optional[SearchResult]:
        """Get document by ID"""
        if self.collection is None:
            return None

        try:
            result = self.collection.get(ids=[id])
            if result and result.get("documents"):
                return SearchResult(
                    id=id,
                    content=result["documents"][0],
                    score=1.0,
                    metadata=result.get("metadatas", [None])[0]
                )
        except Exception:
            pass

        return None

    def count(self) -> int:
        """Get total document count"""
        if self.collection is None:
            return 0
        return self.collection.count()

    def exists(self) -> bool:
        """Check if database exists"""
        if self.client is None:
            return False

        try:
            # Try to get collection - will fail if doesn't exist
            self.client.get_collection(name=self.collection_name)
            return True
        except Exception:
            return False


# Register this plugin
from .plugin import VectorDBFactory
VectorDBFactory.register(VectorDBType.CHROMADB, ChromaDBPlugin)
