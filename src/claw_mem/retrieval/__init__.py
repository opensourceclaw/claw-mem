# claw-mem Retrieval Module — v3.0.0 consolidated (10→4 retrievers)
#
# Consolidated retrievers:
#   keyword.py  — KeywordRetriever (keyword + BM25 + HybridBM25)
#   semantic.py — SemanticRetriever (entity-aware + hybrid)
#   tiered.py   — TieredRetriever (STM/LTM/Archive, was three_tier)
#   smart.py    — SmartRetriever (heuristic + engram + spreading + enhanced)

# === Consolidated imports (v3.0.0) ===
from .keyword import KeywordRetriever
from .semantic_retriever import SemanticRetriever, get_semantic_retriever
from .smart import SmartRetriever, HeuristicRetriever, EnhancedSmartRetriever, DecoupledRetriever
from .tiered import TieredRetriever, MemoryLayer, MemoryResult

# === Legacy imports (deprecated, backward compat) ===
from .bm25_retriever import BM25Retriever
from .embedding_service import EmbeddingService, get_embedding_service
from .hybrid_searcher import HybridSearcher, get_hybrid_searcher
from .query_cache import QueryCache, get_query_cache
from .search_stats import SearchStats, get_search_stats
from .synonym_expander import BUILTIN_SYNONYMS, SynonymExpander, get_synonym_expander

__all__ = [
    # Consolidated
    "KeywordRetriever",
    "SemanticRetriever",
    "get_semantic_retriever",
    "SmartRetriever",
    "HeuristicRetriever",
    "EnhancedSmartRetriever",
    "DecoupledRetriever",
    "TieredRetriever",
    "MemoryLayer",
    "MemoryResult",
    # Legacy
    "EmbeddingService",
    "get_embedding_service",
    "HybridSearcher",
    "get_hybrid_searcher",
    "BM25Retriever",
    "QueryCache",
    "get_query_cache",
    "SynonymExpander",
    "get_synonym_expander",
    "BUILTIN_SYNONYMS",
    "SearchStats",
    "get_search_stats",
]
