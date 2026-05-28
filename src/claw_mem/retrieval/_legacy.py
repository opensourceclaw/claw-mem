"""Legacy retrievers retained for backward compatibility (v4.x.x optimization)."""
import warnings

warnings.warn(
    "The legacy retrievers (BM25Retriever, EmbeddingService, HybridSearcher) "
    "are deprecated and will be removed in v5.0. Use the consolidated "
    "retrievers from keyword.py and semantic_retriever.py instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .bm25_retriever import BM25Retriever      # noqa: E402, F401
from .embedding_service import EmbeddingService  # noqa: E402, F401
from .hybrid_searcher import HybridSearcher      # noqa: E402, F401
