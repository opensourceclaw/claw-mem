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

from .plugin import (
    VectorDBPlugin,
    VectorDBFactory,
    VectorDBType,
    SearchResult
)

from .chromadb_plugin import ChromaDBPlugin

__all__ = [
    "VectorDBPlugin",
    "VectorDBFactory",
    "VectorDBType",
    "SearchResult",
    "ChromaDBPlugin",
]
