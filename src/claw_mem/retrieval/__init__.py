# claw-mem Retrieval Module
# v2.5.0 Semantic Search Integration

from .embedding_service import EmbeddingService, get_embedding_service
from .semantic_retriever import SemanticRetriever, get_semantic_retriever
from .hybrid_searcher import HybridSearcher, get_hybrid_searcher
from .bm25_retriever import BM25Retriever
from .query_cache import QueryCache, get_query_cache
from .synonym_expander import SynonymExpander, get_synonym_expander, BUILTIN_SYNONYMS
from .search_stats import SearchStats, get_search_stats

__all__ = [
    'EmbeddingService',
    'get_embedding_service',
    'SemanticRetriever',
    'get_semantic_retriever',
    'HybridSearcher',
    'get_hybrid_searcher',
    'BM25Retriever',
    'QueryCache',
    'get_query_cache',
    'SynonymExpander',
    'get_synonym_expander',
    'BUILTIN_SYNONYMS',
    'SearchStats',
    'get_search_stats',
]
