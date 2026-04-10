"""
Vector Database Plugin Interface for claw-mem

This module provides an abstract interface for vector database operations,
allowing easy switching between different backends (ChromaDB, Qdrant, Pinecone, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class VectorDBType(Enum):
    """Supported vector database types"""
    CHROMADB = "chromadb"
    QDRANT = "qdrant"
    PINECONE = "pinecone"
    FAISS = "faiss"
    WEAVIATE = "weaviate"


@dataclass
class SearchResult:
    """Standard search result format"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = None


class VectorDBPlugin(ABC):
    """
    Abstract base class for vector database plugins.

    All implementations must inherit from this class and implement
    the required methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the plugin with configuration.

        Args:
            config: Database-specific configuration
        """
        self.config = config

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the vector database.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the vector database"""
        pass

    @abstractmethod
    def add(
        self,
        documents: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add documents to the vector database.

        Args:
            documents: List of text documents
            ids: Unique identifiers for each document
            metadata: Optional metadata for each document

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of search results, sorted by relevance
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs.

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[SearchResult]:
        """
        Retrieve a document by ID.

        Args:
            id: Document ID

        Returns:
            SearchResult if found, None otherwise
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total number of documents.

        Returns:
            Document count
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if the database is initialized.

        Returns:
            True if database exists
        """
        pass


class VectorDBFactory:
    """
    Factory for creating vector database plugin instances.

    Usage:
        # Create ChromaDB plugin
        plugin = VectorDBFactory.create(VectorDBType.CHROMADB, config)

        # Create Qdrant plugin
        plugin = VectorDBFactory.create(VectorDBType.QDRANT, config)
    """

    _plugins: Dict[VectorDBType, type] = {}

    @classmethod
    def register(cls, db_type: VectorDBType, plugin_class: type):
        """Register a new plugin type"""
        cls._plugins[db_type] = plugin_class

    @classmethod
    def create(cls, db_type: VectorDBType, config: Dict[str, Any]) -> VectorDBPlugin:
        """
        Create a plugin instance.

        Args:
            db_type: Type of vector database
            config: Configuration dictionary

        Returns:
            Plugin instance

        Raises:
            ValueError: If db_type is not registered
        """
        if db_type not in cls._plugins:
            raise ValueError(f"Unknown database type: {db_type}. "
                           f"Registered types: {list(cls._plugins.keys())}")

        plugin_class = cls._plugins[db_type]
        return plugin_class(config)

    @classmethod
    def available_types(cls) -> List[VectorDBType]:
        """Get list of available database types"""
        return list(cls._plugins.keys())


# Import and register built-in plugins
# These will be lazily imported to avoid dependencies errors
def _register_plugins():
    """Register built-in plugins"""
    try:
        from .chromadb_plugin import ChromaDBPlugin
        VectorDBFactory.register(VectorDBType.CHROMADB, ChromaDBPlugin)
    except ImportError:
        pass

    try:
        from .qdrant_plugin import QdrantPlugin
        VectorDBFactory.register(VectorDBType.QDRANT, QdrantPlugin)
    except ImportError:
        pass

    try:
        from .pinecone_plugin import PineconePlugin
        VectorDBFactory.register(VectorDBType.PINECONE, PineconePlugin)
    except ImportError:
        pass


# Auto-register plugins on module import
_register_plugins()
