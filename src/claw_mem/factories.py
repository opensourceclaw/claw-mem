# Copyright 2026 Peter Cheng
"""Factory classes for dependency injection (v3.2.0)."""

from typing import Any, Dict, Optional

from .retrieval.base import BaseRetriever
from .storage.base import BaseStorage


class ComponentFactory:
    """
    Centralized factory for dependency injection.
    
    Replaces global singletons with instance-based factories.
    v3.2.0: Eliminates 13 global singletons.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize factory with optional config."""
        self._config = config or {}
        # Cache for created instances (simulates singleton per factory)
        self._instances: Dict[str, Any] = {}

    # ── Retrieval Components ───────────────────────────────────────────────

    def create_synonym_expander(
        self,
        custom_synonyms: Optional[Dict[str, list]] = None,
        enabled: bool = True,
        max_expansions: int = 5
    ) -> "SynonymExpander":
        """Create SynonymExpander instance."""
        from .retrieval.synonym_expander import SynonymExpander
        return SynonymExpander(
            custom_synonyms=custom_synonyms,
            enabled=enabled,
            max_expansions=max_expansions
        )

    def create_query_cache(self, max_size: int = 1000, ttl_seconds: float = 300.0) -> "QueryCache":
        """Create QueryCache instance."""
        from .retrieval.query_cache import QueryCache
        return QueryCache(max_size=max_size, ttl_seconds=ttl_seconds)

    def create_search_stats(self) -> "SearchStats":
        """Create SearchStats instance."""
        from .retrieval.search_stats import SearchStats
        return SearchStats()

    def create_embedding_service(
        self,
        model_name: str = "sentence-transformers",
        device: str = "cpu"
    ) -> "EmbeddingService":
        """Create EmbeddingService instance."""
        from .retrieval.embedding_service import EmbeddingService
        return EmbeddingService(model_name=model_name, device=device)

    def create_hybrid_searcher(self, **kwargs) -> "HybridSearcher":
        """Create HybridSearcher instance."""
        from .retrieval.hybrid_searcher import HybridSearcher
        return HybridSearcher(**kwargs)

    def create_semantic_retriever(self, **kwargs) -> "SemanticRetriever":
        """Create SemanticRetriever instance."""
        from .retrieval.semantic_retriever import SemanticRetriever
        return SemanticRetriever(**kwargs)

    # ── Compression Components ───────────────────────────────────────────────

    def create_memory_compressor(self, config: Optional[Dict] = None) -> "MemoryCompressorV2":
        """Create MemoryCompressorV2 instance."""
        from .compression.memory_compression_v2 import MemoryCompressorV2
        from .compression.memory_compression_v2 import CompressionConfig
        
        compression_config = config or {}
        cfg = CompressionConfig(
            max_tokens=compression_config.get("max_tokens", 2000),
            min_tokens=compression_config.get("min_tokens", 100),
            quality_threshold=compression_config.get("quality_threshold", 0.7),
        )
        return MemoryCompressorV2(config=cfg)

    def create_f5_compressor(self) -> "F5CompressorV2":
        """Create F5CompressorV2 instance."""
        from .compression.f5_v2 import F5CompressorV2
        return F5CompressorV2()

    def create_ultra_compressor(self) -> "UltraCompressor":
        """Create UltraCompressor instance."""
        from .compression.f5_v2 import UltraCompressor
        return UltraCompressor()

    # ── Multimodal Components ────────────────────────────────────────────────

    def create_multimodal_store(self, workspace: str) -> "MultimodalMemoryStore":
        """Create MultimodalMemoryStore instance."""
        from .multimodal.multimodal_memory import MultimodalMemoryStore
        return MultimodalMemoryStore(workspace=workspace)

    # ── Config & Recovery ───────────────────────────────────────────────────

    def create_config_manager(self) -> "ConfigManager":
        """Create ConfigManager instance."""
        from .config_manager import ConfigManager
        return ConfigManager()

    def create_recovery_manager(self, config: Optional[Dict] = None) -> "RecoveryManager":
        """Create RecoveryManager instance."""
        from .recovery import RecoveryManager
        return RecoveryManager(config or {})

    # ── Cache & Reset ──────────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """Clear all cached instances."""
        self._instances.clear()

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached instance by key."""
        return self._instances.get(key)

    def set_cached(self, key: str, instance: Any) -> None:
        """Cache an instance."""
        self._instances[key] = instance


# Default global factory (for backward compatibility)
_default_factory: Optional[ComponentFactory] = None


def get_default_factory() -> ComponentFactory:
    """Get default global factory instance."""
    global _default_factory
    if _default_factory is None:
        _default_factory = ComponentFactory()
    return _default_factory


def reset_default_factory() -> None:
    """Reset default factory (for testing)."""
    global _default_factory
    _default_factory = None


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

            return EpisodicStorage(
                workspace=workspace, **{k: v for k, v in kwargs.items() if k != "workspace"}
            )
        elif storage_type == "semantic":
            from .storage.semantic import SemanticStorage

            return SemanticStorage(
                workspace=workspace, **{k: v for k, v in kwargs.items() if k != "workspace"}
            )
        elif storage_type == "procedural":
            from .storage.procedural import ProceduralStorage

            return ProceduralStorage(
                workspace=workspace, **{k: v for k, v in kwargs.items() if k != "workspace"}
            )
        raise ValueError(f"Unknown storage type: {storage_type}")
