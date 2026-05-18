# Copyright 2026 Peter Cheng
"""Factory classes for dependency injection (v3.0.0-rc.5)."""

from typing import Optional
from .retrieval.base import BaseRetriever
from .storage.base import BaseStorage


class RetrieverFactory:
    """Factory for creating retrievers."""

    @staticmethod
    def create(retriever_type: str = "hybrid", **kwargs) -> BaseRetriever:
        if retriever_type == "hybrid":
            from .retrieval.hybrid_searcher import HybridSearcher
            return HybridSearcher(**kwargs)
        elif retriever_type == "bm25":
            from .retrieval.bm25_retriever import BM25Retriever
            return BM25Retriever(**kwargs)
        elif retriever_type == "keyword":
            from .retrieval.keyword import KeywordRetriever
            return KeywordRetriever()
        elif retriever_type == "engram":
            from .retrieval.engram import EngramIndex
            return EngramIndex(**kwargs)
        raise ValueError(f"Unknown retriever type: {retriever_type}")


class StorageFactory:
    """Factory for creating storage backends."""

    @staticmethod
    def create(storage_type: str = "file", **kwargs) -> BaseStorage:
        workspace = kwargs.get("workspace", None)
        if storage_type == "episodic":
            from .storage.episodic import EpisodicStorage
            return EpisodicStorage(workspace=workspace, **{
                k: v for k, v in kwargs.items() if k != "workspace"
            })
        elif storage_type == "semantic":
            from .storage.semantic import SemanticStorage
            return SemanticStorage(workspace=workspace, **{
                k: v for k, v in kwargs.items() if k != "workspace"
            })
        elif storage_type == "procedural":
            from .storage.procedural import ProceduralStorage
            return ProceduralStorage(workspace=workspace, **{
                k: v for k, v in kwargs.items() if k != "workspace"
            })
        raise ValueError(f"Unknown storage type: {storage_type}")
