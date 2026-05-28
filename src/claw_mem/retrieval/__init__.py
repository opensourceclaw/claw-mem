# claw-mem Retrieval Module — v3.0.0 consolidated (10→4 retrievers)
#
# Consolidated retrievers:
#   keyword.py  — KeywordRetriever (keyword + BM25 + HybridBM25)
#   semantic.py — SemanticRetriever (entity-aware + hybrid)
#   tiered.py   — TieredRetriever (STM/LTM/Archive, was three_tier)
#   smart.py    — SmartRetriever (heuristic + enhanced)

# === Consolidated imports (v3.0.0 → v3.2.0: direct from source) ===
from .keyword import KeywordRetriever
from .semantic_retriever import SemanticRetriever
from .heuristic_retriever import SmartRetriever, HeuristicRetriever
from .three_tier import TieredRetriever, MemoryLayer, MemoryResult

# === Legacy imports (via _legacy.py — deprecation-wrapped) ===
from ._legacy import BM25Retriever, EmbeddingService, HybridSearcher
from .query_cache import QueryCache, get_query_cache
from .search_stats import SearchStats, get_search_stats
from .synonym_expander import BUILTIN_SYNONYMS, SynonymExpander
from .query_reconstructor import QueryReconstructor
from .hybrid_router import HybridRouter, QueryType

__all__ = [
    # Consolidated
    "KeywordRetriever",
    "SemanticRetriever",
    "SmartRetriever",
    "HeuristicRetriever",
    "TieredRetriever",
    "MemoryLayer",
    "MemoryResult",
    # Legacy
    "EmbeddingService",
    "HybridSearcher",
    "BM25Retriever",
    "QueryCache",
    "get_query_cache",
    "SynonymExpander",
    "BUILTIN_SYNONYMS",
    "SearchStats",
    "get_search_stats",
    # v4.8.0: Query reconstruction + hybrid routing
    "QueryReconstructor",
    "HybridRouter",
    "QueryType",
]
