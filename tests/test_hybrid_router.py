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

"""Tests for HybridRouter + QueryType (F2, v4.8.0)."""

from unittest.mock import MagicMock

import pytest
from claw_mem.retrieval.hybrid_router import HybridRouter, QueryType


# ── Helpers ────────────────────────────────────────────────────────────

def _make_result(idx: int, content: str = "", score: float = 1.0) -> dict:
    return {
        "id": f"mem_{idx}",
        "content": content or f"memory content {idx}",
        "text": content or f"memory content {idx}",
        "created_at": "2026-01-01T00:00:00",
        "source": "test",
        "memory_type": "episodic",
        "type": "episodic",
        "metadata": {},
        "tags": [],
        "score": score,
    }


def _make_manager(**kwargs):
    """Create a mock MemoryManager with configurable retriever and graph."""
    mgr = MagicMock()

    # Default retriever: returns 3 results
    defaults = [_make_result(1, "JWT token fix"), _make_result(2, "JWT auth"), _make_result(3, "API")]
    mgr.retriever.search = MagicMock(return_value=list(defaults))

    mgr.episodic = MagicMock()
    mgr.semantic = MagicMock()
    mgr.procedural = MagicMock()
    mgr.enable_graph = False
    mgr.graph = None

    # Apply overrides
    for k, v in kwargs.items():
        setattr(mgr, k, v)

    return mgr


# ── Mock LLM for classification ────────────────────────────────────────

class _ClassifyLLM:
    """Mock LLM that returns a fixed classification label."""

    def __init__(self, label: str = ""):
        self.label = label

    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        return self.label


class _FailingLLM:
    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        return ""


# ── QueryType enum ─────────────────────────────────────────────────────

class TestQueryType:
    def test_enum_values(self):
        assert QueryType.FACT.value == "fact"
        assert QueryType.SEMANTIC.value == "semantic"
        assert QueryType.RELATION.value == "relation"


# ── Classification: rule-based ──────────────────────────────────────────

class TestRuleClassify:
    @pytest.mark.parametrize("query,expected", [
        ("who wrote this", QueryType.FACT),
        ("what is the password", QueryType.FACT),
        ("where is the config file", QueryType.FACT),
        ("when did the meeting happen", QueryType.FACT),
        ("how many users are there", QueryType.FACT),
        ("密码是什么", QueryType.FACT),
        ("设置在哪里", QueryType.FACT),
        ("配置信息", QueryType.FACT),
        ("是谁做了这个", QueryType.FACT),
        ("哪个版本", QueryType.FACT),
    ])
    def test_classify_fact(self, query, expected):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)  # No LLM → rule only
        assert router.classify(query) == expected

    @pytest.mark.parametrize("query,expected", [
        ("how to fix the bug", QueryType.SEMANTIC),
        ("why is this slow", QueryType.SEMANTIC),
        ("explain the architecture", QueryType.SEMANTIC),
        ("discuss design patterns", QueryType.SEMANTIC),
        ("analyze the performance", QueryType.SEMANTIC),
        ("怎么修复这个问题", QueryType.SEMANTIC),
        ("为什么这么慢", QueryType.SEMANTIC),
        ("解释一下架构", QueryType.SEMANTIC),
        ("方案讨论", QueryType.SEMANTIC),
        ("如何部署", QueryType.SEMANTIC),
    ])
    def test_classify_semantic(self, query, expected):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        assert router.classify(query) == expected

    @pytest.mark.parametrize("query,expected", [
        ("relation between A and B", QueryType.RELATION),
        ("vs comparison", QueryType.RELATION),
        ("difference between X and Y", QueryType.RELATION),
        ("link between modules", QueryType.RELATION),
        ("A和B的关系", QueryType.RELATION),
        ("关联分析的结果", QueryType.RELATION),
        ("比较两个方案", QueryType.RELATION),
        ("影响分析", QueryType.RELATION),
    ])
    def test_classify_relation(self, query, expected):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        assert router.classify(query) == expected

    def test_default_is_semantic(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        assert router.classify("hello world") == QueryType.SEMANTIC

    def test_empty_query_defaults_semantic(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        assert router.classify("") == QueryType.SEMANTIC


# ── Classification: LLM-based ──────────────────────────────────────────

class TestLLMClassify:
    def test_llm_classifies_fact(self):
        llm = _ClassifyLLM("fact")
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=llm)
        result = router.classify("hello world")  # Would be SEMANTIC by rule
        assert result == QueryType.FACT

    def test_llm_classifies_semantic(self):
        llm = _ClassifyLLM("semantic")
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=llm)
        assert router.classify("what is the password") == QueryType.SEMANTIC

    def test_llm_classifies_relation(self):
        llm = _ClassifyLLM("relation")
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=llm)
        assert router.classify("hello") == QueryType.RELATION

    def test_llm_returns_empty_falls_back_to_rule(self):
        llm = _ClassifyLLM("")
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=llm)
        # "who wrote this" should be FACT by rule
        assert router.classify("who wrote this") == QueryType.FACT

    def test_llm_fails_falls_back_to_rule(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=_FailingLLM())
        assert router.classify("who wrote this") == QueryType.FACT

    def test_llm_unknown_label_falls_back_to_rule(self):
        llm = _ClassifyLLM("unknown")
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=llm)
        assert router.classify("who wrote this") == QueryType.FACT


# ── Routing ────────────────────────────────────────────────────────────

class TestRouting:
    def test_route_fact_calls_keyword_search(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        results = router.route("who wrote this", limit=5)
        mgr.retriever.search.assert_called_once()
        assert len(results) == 3

    def test_route_semantic_uses_multi_query(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        results = router.route("how to fix the memory leak", limit=5)
        # Should call search at least once (original query)
        assert mgr.retriever.search.call_count >= 1
        assert len(results) <= 5
        # Each result should have expected keys
        for r in results:
            assert "id" in r or "content" in r

    def test_route_relation_without_graph_falls_back_to_fact(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        results = router.route("relation between A and B", limit=5)
        mgr.retriever.search.assert_called_once()
        assert len(results) == 3

    def test_route_relation_with_graph(self):
        from dataclasses import dataclass

        @dataclass
        class MockNode:
            id: str = "n1"
            content: str = "graph result"
            text: str = "graph result"
            timestamp: str = "2026-01-01"
            source: str = "graph"
            type: str = "fact"
            metadata: dict = None
            tags: list = None
            def __post_init__(self):
                if self.metadata is None:
                    self.metadata = {}
                if self.tags is None:
                    self.tags = []

        @dataclass
        class MockGraphResult:
            node: MockNode
            score: float = 0.95

        mock_graph = MagicMock()
        mock_graph.retrieve = MagicMock(return_value=[MockGraphResult(node=MockNode())])

        mgr = _make_manager(enable_graph=True, graph=mock_graph)
        router = HybridRouter(manager=mgr)
        results = router.route("relation between A and B", limit=5)

        mock_graph.retrieve.assert_called_once()
        assert len(results) == 1
        assert results[0]["content"] == "graph result"

    def test_route_relation_graph_returns_none_falls_back(self):
        mock_graph = MagicMock()
        mock_graph.retrieve = MagicMock(return_value=[])

        mgr = _make_manager(enable_graph=True, graph=mock_graph)
        router = HybridRouter(manager=mgr)
        results = router.route("relation between A and B", limit=5)

        # Should fall back to keyword search
        mgr.retriever.search.assert_called_once()
        assert len(results) == 3

    def test_route_relation_graph_throws_falls_back(self):
        mock_graph = MagicMock()
        mock_graph.retrieve = MagicMock(side_effect=RuntimeError("graph error"))

        mgr = _make_manager(enable_graph=True, graph=mock_graph)
        router = HybridRouter(manager=mgr)
        results = router.route("relation between A and B", limit=5)

        # Should fall back to keyword search gracefully
        mgr.retriever.search.assert_called_once()
        assert len(results) == 3


# ── Merge weighted ─────────────────────────────────────────────────────

class TestMergeWeighted:
    def test_deduplicates_by_id(self):
        r1 = _make_result(1, "JWT fix", score=0.9)
        r2 = _make_result(1, "JWT fix", score=0.5)  # Duplicate ID, lower score
        r3 = _make_result(2, "auth", score=0.8)

        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        pipe_results = {
            "original": [r1],
            "variant_1": [dict(r2), dict(r3)],
        }
        merged = router._merge_weighted(pipe_results, top_k=10)
        ids = [m["id"] for m in merged]
        assert ids.count("mem_1") == 1
        assert "mem_2" in ids

    def test_original_boosted(self):
        r1 = _make_result(1, "orig content", score=0.5)
        r2 = _make_result(1, "var content", score=0.9)  # Higher raw score

        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        pipe_results = {"original": [r1], "variant_1": [r2]}
        merged = router._merge_weighted(pipe_results, top_k=10)
        # The entry in merged should be from original (boosted 0.5*1.2=0.6)
        assert merged[0]["id"] == "mem_1"
        # Check which source won - original with boost 0.6 vs variant 0.9
        assert merged[0]["score"] > 0.5  # Boost is applied to original

    def test_top_k_limit(self):
        results = []
        for i in range(20):
            results.append(_make_result(i, score=float(20 - i)))
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        pipe_results = {"original": results}
        merged = router._merge_weighted(pipe_results, top_k=5)
        assert len(merged) == 5

    def test_no_id_results_handled(self):
        r = {"content": "no-id result"}
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        pipe_results = {"original": [r]}
        merged = router._merge_weighted(pipe_results, top_k=5)
        assert len(merged) == 1
        assert merged[0]["content"] == "no-id result"


# ── Constructor ────────────────────────────────────────────────────────

class TestRouterInit:
    def test_constructor_stores_manager(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        assert router._manager is mgr

    def test_constructor_stores_llm(self):
        llm = _ClassifyLLM()
        mgr = _make_manager()
        router = HybridRouter(manager=mgr, llm_provider=llm)
        assert router._llm is llm

    def test_reconstructor_lazy_init(self):
        mgr = _make_manager()
        router = HybridRouter(manager=mgr)
        assert router._reconstructor is None
        recon = router.reconstructor
        assert recon is not None
        assert router._reconstructor is recon
