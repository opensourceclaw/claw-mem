# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Hybrid Query Router (v4.8.0)

Classifies incoming queries into FACT / SEMANTIC / RELATION types and
routes them through the optimal retrieval pipeline for each category.

- FACT queries (what/who/where): precise keyword matching
- SEMANTIC queries (how/why/explain): multi-query reconstruction + weighted merge
- RELATION queries (vs/link/relation): concept graph traversal (falls back to FACT)
"""

import re
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING


def _has_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    return bool(re.search(r"[\u4e00-\u9fff\u3040-\u309f\uac00-\ud7af]", text))

if TYPE_CHECKING:
    from ..memory_manager import MemoryManager


class QueryType(Enum):
    """Query classification: fact, semantic, or relation."""
    FACT = "fact"
    SEMANTIC = "semantic"
    RELATION = "relation"


# ── Rule-based classification patterns ───────────────────────────────────────

_FACT_PATTERNS_ZH = {
    "密码", "设置", "配置", "是谁", "在哪里", "什么时候", "多少个", "哪个",
    "什么", "谁", "哪里", "何时", "日期", "时间", "地址", "位置", "电话",
}
_FACT_PATTERNS_EN = {
    "password", "setting", "config", "who", "where", "when", "how many",
    "what is", "is the", "are the", "which",
}
_SEMANTIC_PATTERNS_ZH = {
    "怎么", "为什么", "解释", "讨论", "方案", "分析", "总结", "评估",
    "如何", "怎么样", "探讨", "建议", "规划", "设计", "实现", "优化",
    "改进", "修复", "解决", "指南", "教程", "原理", "流程",
}
_SEMANTIC_PATTERNS_EN = {
    "how", "why", "explain", "discuss", "analyze", "describe", "evaluate",
    "summarize", "suggest", "recommend", "design", "implement", "optimize",
    "improve", "fix", "solve", "guide", "tutorial", "principle", "approach",
    "strategy",
}
_RELATION_PATTERNS_ZH = {
    "关系", "关联", "区别", "比较", "vs", "联系", "和", "与",
    "连接", "依赖", "影响", "对比",
}
_RELATION_PATTERNS_EN = {
    "relation", "relationship", "link", "connection", "vs", "versus",
    "compare", "difference", "between", "depend", "affect", "contrast",
    "correlation",
}

_CLASSIFY_SYSTEM = (
    "You are a query classifier. Classify the given query into exactly one "
    "of three types: fact, semantic, or relation.\n\n"
    "- fact: factual lookup (who, what, where, when, how many, config, settings)\n"
    "- semantic: conceptual (how, why, explain, analyze, discuss, summarize)\n"
    "- relation: comparing or linking (relation, vs, difference, link, connection)\n\n"
    "Reply with ONLY one word: fact, semantic, or relation."
)


class HybridRouter:
    """Routes queries through optimal retrieval pipelines.

    Classifies queries into FACT / SEMANTIC / RELATION and dispatches to
    the appropriate retrieval strategy.

    Usage:
        router = HybridRouter(manager=memory_manager, llm_provider=llm)
        results = router.route("how to fix the memory leak")
        # → List[Dict] in standard MemoryManager.search() format
    """

    def __init__(self, manager: "MemoryManager", llm_provider=None):
        """Initialize HybridRouter.

        Args:
            manager: MemoryManager instance (access to retriever, graph, etc.).
            llm_provider: Optional LLMProvider for classification.
        """
        self._manager = manager
        self._llm = llm_provider
        # Lazily initialized
        self._reconstructor = None

    @property
    def reconstructor(self):
        """Lazy-init QueryReconstructor shared with MemoryManager."""
        if self._reconstructor is None:
            from .query_reconstructor import QueryReconstructor
            self._reconstructor = QueryReconstructor(llm_provider=self._llm)
        return self._reconstructor

    # ── Classification ─────────────────────────────────────────────────

    def classify(self, query: str) -> QueryType:
        """Classify query into FACT, SEMANTIC, or RELATION.

        Args:
            query: Search query string.

        Returns:
            QueryType classification.
        """
        query_stripped = query.strip()
        if not query_stripped:
            return QueryType.SEMANTIC

        # Try LLM classification first
        if self._llm is not None:
            llm_result = self._llm_classify(query_stripped)
            if llm_result is not None:
                return llm_result

        # Fallback to rule-based classification
        return self._rule_classify(query_stripped)

    def _llm_classify(self, query: str) -> Optional[QueryType]:
        """LLM-based classification; returns None on failure."""
        try:
            prompt = (
                f"Classify this query into one of: fact, semantic, relation.\n"
                f"Query: '{query}'\n\n"
                f"Reply with ONLY the classification word."
            )
            result = self._llm.generate(prompt, system=_CLASSIFY_SYSTEM, max_tokens=16)
            if not result or not result.strip():
                return None
            label = result.strip().lower()
            if "semantic" in label:
                return QueryType.SEMANTIC
            if "relation" in label:
                return QueryType.RELATION
            if "fact" in label:
                return QueryType.FACT
            return None
        except Exception:
            return None

    def _rule_classify(self, query: str) -> QueryType:
        """Rule-based classification using keyword patterns.

        Priority: FACT > RELATION > SEMANTIC (default).
        Uses tokenization for Chinese to avoid substring false matches
        (e.g. "什么" matching inside "为什么").
        """
        query_lower = query.lower()

        # Tokenize Chinese queries for word-boundary matching
        tokens = self._tokenize_zh(query) if _has_cjk(query) else []

        # Check FACT patterns
        for pat in _FACT_PATTERNS_ZH:
            if tokens and pat in tokens:
                return QueryType.FACT
            elif not tokens and pat in query:
                return QueryType.FACT
        for pat in _FACT_PATTERNS_EN:
            if pat in query_lower:
                return QueryType.FACT

        # Check RELATION patterns
        for pat in _RELATION_PATTERNS_ZH:
            if tokens and pat in tokens:
                return QueryType.RELATION
            elif not tokens and pat in query:
                return QueryType.RELATION
        for pat in _RELATION_PATTERNS_EN:
            if pat in query_lower:
                return QueryType.RELATION

        # Check SEMANTIC patterns
        for pat in _SEMANTIC_PATTERNS_ZH:
            if tokens and pat in tokens:
                return QueryType.SEMANTIC
            elif not tokens and pat in query:
                return QueryType.SEMANTIC
        for pat in _SEMANTIC_PATTERNS_EN:
            if pat in query_lower:
                return QueryType.SEMANTIC

        # Default to SEMANTIC
        return QueryType.SEMANTIC

    @staticmethod
    def _tokenize_zh(text: str) -> List[str]:
        """Tokenize Chinese text using jieba; fallback to character-level."""
        try:
            import jieba
            return list(jieba.cut(text))
        except ImportError:
            # Simple fallback: split on whitespace + extract CJK chars
            tokens: List[str] = []
            buf = ""
            for ch in text:
                if _has_cjk(ch):
                    if buf:
                        tokens.append(buf)
                        buf = ""
                    tokens.append(ch)
                elif ch.isspace():
                    if buf:
                        tokens.append(buf)
                        buf = ""
                else:
                    buf += ch
            if buf:
                tokens.append(buf)
            return tokens

    # ── Routing ─────────────────────────────────────────────────────────

    def route(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Classify query and route to optimal retrieval pipeline.

        Args:
            query: Search query string.
            memory_type: Optional memory type filter.
            limit: Maximum number of results.

        Returns:
            List of memory dicts in standard search() format.
        """
        qtype = self.classify(query)

        if qtype == QueryType.FACT:
            return self._search_fact(query, memory_type=memory_type, limit=limit)
        elif qtype == QueryType.SEMANTIC:
            return self._search_semantic(query, memory_type=memory_type, limit=limit)
        else:  # RELATION
            return self._search_relation(query, memory_type=memory_type, limit=limit)

    # ── FACT pipeline: keyword exact match ──────────────────────────────

    def _search_fact(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Fact query: direct keyword retrieval with exact matching."""
        mgr = self._manager
        return mgr.retriever.search(
            query,
            mgr.episodic,
            mgr.semantic,
            mgr.procedural,
            memory_type=memory_type,
            limit=limit,
        )

    # ── SEMANTIC pipeline: multi-query + weighted merge ─────────────────

    def _search_semantic(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Semantic query: multi-query reconstruction with weighted merge.

        1. Generate query variants via QueryReconstructor.
        2. Search with each variant via KeywordRetriever.
        3. Merge results by highest score, deduplicating on id.
        """
        variants = self.reconstructor.reconstruct(query)
        mgr = self._manager

        pipe_results: Dict[str, List[Dict]] = {}

        # Original query (primary)
        pipe_results["original"] = mgr.retriever.search(
            query,
            mgr.episodic,
            mgr.semantic,
            mgr.procedural,
            memory_type=memory_type,
            limit=limit * 2,
        )

        # Variant queries (secondary, with dampened scores)
        for i, v in enumerate(variants[1:], start=1):  # Skip original
            if v.lower() == query.lower():
                continue
            results = mgr.retriever.search(
                v,
                mgr.episodic,
                mgr.semantic,
                mgr.procedural,
                memory_type=memory_type,
                limit=limit,
            )
            pipe_results[f"variant_{i}"] = results

        return self._merge_weighted(pipe_results, top_k=limit)

    # ── RELATION pipeline: graph traversal ──────────────────────────────

    def _search_relation(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Relation query: concept graph traversal, fallback to FACT.

        1. Try ConceptMediatedGraph.retrieve() if graph is available.
        2. Convert RetrievalResult nodes to dict format.
        3. Fallback to FACT pipeline if graph is unavailable or returns nothing.
        """
        mgr = self._manager

        # Check if graph is enabled and available
        if mgr.enable_graph and mgr.graph is not None:
            try:
                graph_results = mgr.graph.retrieve(query, k=limit)
                if graph_results:
                    return [
                        self._graph_result_to_dict(r, mgr)
                        for r in graph_results[:limit]
                    ]
            except Exception:
                pass

        # Fallback to FACT pipeline
        return self._search_fact(query, memory_type=memory_type, limit=limit)

    @staticmethod
    def _graph_result_to_dict(result, manager) -> Dict:
        """Convert a graph RetrievalResult to a standard search dict."""
        node = result.node
        # Build dict compatible with keyword search results
        d = {
            "id": getattr(node, "id", "") or getattr(node, "node_id", ""),
            "content": getattr(node, "content", "") or getattr(node, "text", ""),
            "text": getattr(node, "text", "") or getattr(node, "content", ""),
            "created_at": (
                getattr(node, "timestamp", "")
                or getattr(node, "created_at", "")
            ),
            "source": getattr(node, "source", "") or getattr(node, "session_id", ""),
            "memory_type": getattr(node, "type", "semantic"),
            "type": getattr(node, "type", "semantic"),
            "metadata": getattr(node, "metadata", {}) or {},
            "tags": getattr(node, "tags", []) or [],
            "score": result.score,
        }
        # Ensure metadata is a dict
        if not isinstance(d["metadata"], dict):
            d["metadata"] = {}
        # Ensure tags is a list
        if isinstance(d["tags"], str):
            d["tags"] = [t.strip() for t in d["tags"].split(",") if t.strip()]
        return d

    # ── Result merging ──────────────────────────────────────────────────

    def _merge_weighted(
        self,
        pipe_results: Dict[str, List[Dict]],
        top_k: int = 10,
    ) -> List[Dict]:
        """Merge results from multiple pipelines by highest score.

        Strategy:
          - Same id across pipelines: keep the entry with the highest score.
          - Primary original query results are ranked first (sort key prefix).
          - Sort by key rank then score, take top-k.

        Args:
            pipe_results: Mapping of pipe_name → List[Dict] results.
            top_k: Maximum number of results to return.

        Returns:
            Merged and deduplicated list of memory dicts.
        """
        # Rank ordering: "original" first, then variants
        pipe_order = list(pipe_results.keys())
        pipe_rank = {name: i for i, name in enumerate(pipe_order)}

        merged: Dict[str, Dict] = {}

        for pipe_name, results in pipe_results.items():
            for r in results:
                rid = r.get("id", "")
                score = r.get("score", 0)
                if isinstance(score, (int, float)):
                    # Boost original query results
                    if pipe_name == "original":
                        score = score * 1.2
                else:
                    score = 0

                if rid and rid in merged:
                    # Keep the entry with the higher score
                    existing_score = merged[rid].get("score", 0)
                    if score > existing_score:
                        r_copy = dict(r)
                        r_copy["score"] = score
                        merged[rid] = r_copy
                elif rid:
                    r_copy = dict(r)
                    r_copy["score"] = score
                    merged[rid] = r_copy
                else:
                    # No id — use content as key for deduplication
                    content_key = r.get("content", "")
                    if content_key and content_key in merged:
                        existing_score = merged[content_key].get("score", 0)
                        if score > existing_score:
                            r_copy = dict(r)
                            r_copy["score"] = score
                            merged[content_key] = r_copy
                    elif content_key:
                        r_copy = dict(r)
                        r_copy["score"] = score
                        merged[content_key] = r_copy

        # Sort: original pipe results first, then by score descending
        def _sort_key(item: tuple) -> tuple:
            rid, rec = item
            rec_pipe = rec.get("_pipe", "original")
            return (pipe_rank.get(rec_pipe, 99), -rec.get("score", 0))

        sorted_items = sorted(merged.items(), key=_sort_key)
        return [item[1] for item in sorted_items[:top_k]]


__all__ = ["HybridRouter", "QueryType"]
