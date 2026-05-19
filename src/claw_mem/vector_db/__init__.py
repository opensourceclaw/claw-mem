"""
Vector Database Plugins for claw-mem

This package provides pluggable vector database backends:
- ChromaDB: Local-first, embedded (default for MVP)
- Qdrant: High-performance, local or cloud
- Pinecone: Cloud-native, production-ready

Usage:
    from claw_mem.vector_db import VectorDBFactory, VectorDBType

    # Create a plugin
    plugin = VectorDBFactory.create(
        VectorDBType.CHROMADB,
        {"path": "./vector_store", "collection_name": "memories"}
    )

    # Use the plugin
    plugin.connect()
    plugin.add(["memory content"], ["memory_id_1"])
    results = plugin.search("query", top_k=5)
"""

from .chromadb_plugin import ChromaDBPlugin
from .plugin import SearchResult, VectorDBFactory, VectorDBPlugin, VectorDBType

__all__ = [
    "VectorDBPlugin",
    "VectorDBFactory",
    "VectorDBType",
    "SearchResult",
    "ChromaDBPlugin",
]
