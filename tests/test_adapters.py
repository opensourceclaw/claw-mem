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

"""Tests for claw_mem adapter abstraction layer."""

import os
import time
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from claw_mem.adapters import (
    AdapterError,
    AdapterRegistry,
    BaseAdapter,
    OpenClawAdapter,
    SearchCache,
    V1Strategy,
    V2Strategy,
)


# ---- Helpers ----------------------------------------------------------------

def _make_mock_result(id_str, content, score=0.8, metadata=None, text=None):
    """Create a dict that looks like a MemoryManager.search() result."""
    r = {"id": id_str, "content": content, "score": score}
    if metadata is not None:
        r["metadata"] = metadata
    if text is not None:
        r["text"] = text
    return r


def _make_mock_manager():
    """Create a mock MemoryManager with standard responses."""
    mgr = MagicMock()
    mgr.search.return_value = [
        _make_mock_result("mem-1", "Memory one content", score=0.95, metadata={"tag": "test"}),
        _make_mock_result("mem-2", "Memory two content", score=0.85, metadata={"key": "val"}),
    ]
    mgr.store.return_value = "new-id-1234"
    mgr.get.return_value = {"id": "mem-1", "content": "Memory one content", "metadata": {"tag": "test"}}
    mgr.delete.return_value = True
    mgr.get_stats.return_value = {"episodic": 10, "semantic": 5, "procedural": 2}
    return mgr


# ---- SearchCache ------------------------------------------------------------

class TestSearchCache:
    def test_get_set_hit(self):
        cache = SearchCache(max_size=10, ttl_sec=3600)
        cache.set("hello", 5, "episodic", [{"id": "1"}])
        result = cache.get("hello", 5, "episodic")
        assert result == [{"id": "1"}]

    def test_get_miss_different_params(self):
        cache = SearchCache(max_size=10, ttl_sec=3600)
        cache.set("hello", 5, "episodic", [{"id": "1"}])
        assert cache.get("hello", 10, "episodic") is None
        assert cache.get("world", 5, "episodic") is None
        assert cache.get("hello", 5, "semantic") is None

    def test_ttl_expiry(self):
        cache = SearchCache(max_size=10, ttl_sec=0.01)
        cache.set("hello", 5, "episodic", [{"id": "1"}])
        time.sleep(0.02)
        assert cache.get("hello", 5, "episodic") is None

    def test_invalidate_clears_all(self):
        cache = SearchCache(max_size=10, ttl_sec=3600)
        cache.set("a", 5, "episodic", [1])
        cache.set("b", 5, "episodic", [2])
        cache.invalidate()
        assert cache.get("a", 5, "episodic") is None
        assert cache.get("b", 5, "episodic") is None

    def test_lru_eviction(self):
        cache = SearchCache(max_size=2, ttl_sec=3600)
        cache.set("a", 5, "episodic", [1])
        cache.set("b", 5, "episodic", [2])
        cache.set("c", 5, "episodic", [3])  # should evict oldest
        # Oldest should be evicted; newer two remain
        hits = sum(1 for q in ["a", "b", "c"] if cache.get(q, 5, "episodic") is not None)
        assert hits == 2


# ---- BaseAdapter ABC --------------------------------------------------------

class TestBaseAdapter:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            BaseAdapter()

    def test_concrete_subclass_must_implement_all(self):
        class Partial(BaseAdapter):
            def get_version(self): pass

        with pytest.raises(TypeError):
            Partial()


# ---- V2Strategy -------------------------------------------------------------

class TestV2Strategy:
    def test_get_version(self):
        s = V2Strategy()
        assert s.get_version() == "2.8.0"

    def test_get_initialize_response(self):
        s = V2Strategy()
        resp = s.get_initialize_response()
        assert resp["status"] == "ok"
        assert resp["message"] == "initialized"
        assert resp["version"] == "2.6.0"

    def test_format_search_result_dict(self):
        s = V2Strategy()
        r = _make_mock_result("abc", "hello world", score=0.9, metadata={"type": "test"})
        formatted = s.format_search_result(r)
        assert formatted["id"] == "abc"
        assert formatted["text"] == "hello world"
        assert formatted["score"] == 0.9
        assert formatted["metadata"] == {"type": "test"}

    def test_format_search_result_fallback_text_to_content(self):
        s = V2Strategy()
        r = {"id": "x", "text": "direct text", "score": 0.5, "metadata": {}}
        formatted = s.format_search_result(r)
        assert formatted["text"] == "direct text"

    def test_format_search_result_uses_content_when_no_text(self):
        s = V2Strategy()
        r = {"id": "x", "content": "only content", "score": 0.5}
        formatted = s.format_search_result(r)
        assert formatted["text"] == "only content"

    def test_build_context_with_results(self):
        s = V2Strategy()
        mgr = _make_mock_manager()
        mgr.search.return_value = [_make_mock_result("1", "test memory")]

        with patch("claw_mem.context_injection.format_memory_context", return_value="--- formatted ---"):
            with patch("claw_mem.context_injection.LayeredContextFormatter") as mock_layered:
                mock_formatter = MagicMock()
                mock_formatter.format.return_value = "--- layered ---"
                mock_formatter.token_report.return_value = {
                    "full_tokens": 100, "layered_tokens": 50,
                    "saved_tokens": 50, "savings_pct": 50.0,
                    "layers_active": ["core"],
                }
                mock_layered.return_value = mock_formatter

                result = s.build_context(mgr, {"topK": 5, "query": "test query"})

                assert result["count"] == 1
                assert len(result["context"]) == 2
                assert "--- layered ---" in result["context"]
                assert "--- formatted ---" in result["context"]
                assert "token_info" in result

    def test_build_context_empty_results(self):
        s = V2Strategy()
        mgr = _make_mock_manager()
        mgr.search.return_value = []

        with patch("claw_mem.context_injection.LayeredContextFormatter") as mock_layered:
            mock_formatter = MagicMock()
            mock_formatter.format.return_value = "--- layered ---"
            mock_formatter.token_report.return_value = {"full_tokens": 100, "layered_tokens": 0}
            mock_layered.return_value = mock_formatter

            result = s.build_context(mgr, {"topK": 5, "query": "test"})

            assert result["count"] == 0
            assert len(result["context"]) == 1
            assert "--- layered ---" in result["context"][0]

    def test_build_context_exception(self):
        s = V2Strategy()
        mgr = MagicMock()
        mgr.search.side_effect = RuntimeError("search failed")
        with patch("claw_mem.context_injection.LayeredContextFormatter") as mock_layered:
            mock_formatter = MagicMock()
            mock_formatter.token_report.return_value = {}
            mock_formatter.format.return_value = ""
            mock_layered.return_value = mock_formatter

            result = s.build_context(mgr, {"query": "test"})
            assert result["context"] == []
            assert result["count"] == 0
            assert "error" in result

    def test_resolve_flush_plan_small_memory(self):
        s = V2Strategy()
        mgr = MagicMock()
        mgr.get_stats.return_value = {"episodic": 10, "semantic": 5, "procedural": 2}
        result = s.resolve_flush_plan(mgr, {})
        assert result["softThresholdTokens"] == 100000
        assert result["forceFlushTranscriptBytes"] == 500000
        assert result["reserveTokensFloor"] == 20000
        assert result["totalMemories"] == 17
        assert "relativePath" in result
        assert "prompt" in result
        assert "systemPrompt" in result
        assert "stats" in result

    def test_resolve_flush_plan_large_memory(self):
        s = V2Strategy()
        mgr = MagicMock()
        mgr.get_stats.return_value = {"episodic": 400, "semantic": 100, "procedural": 50}
        result = s.resolve_flush_plan(mgr, {})
        assert result["softThresholdTokens"] == 80000
        assert result["forceFlushTranscriptBytes"] == 400000
        assert result["reserveTokensFloor"] == 15000
        assert result["totalMemories"] == 550

    def test_resolve_flush_plan_exception(self):
        s = V2Strategy()
        mgr = MagicMock()
        mgr.get_stats.side_effect = RuntimeError("stats failed")
        result = s.resolve_flush_plan(mgr, {})
        assert "error" in result


# ---- V1Strategy -------------------------------------------------------------

class TestV1Strategy:
    def test_get_version(self):
        s = V1Strategy()
        assert s.get_version() == "2.0.0"

    def test_get_initialize_response(self):
        s = V1Strategy()
        resp = s.get_initialize_response()
        assert resp["status"] == "initialized"
        assert resp["version"] == "2.0.0"

    def test_format_search_result_no_metadata(self):
        s = V1Strategy()
        r = _make_mock_result("abc", "hello world", score=0.9, metadata={"type": "test"})
        formatted = s.format_search_result(r)
        assert formatted["id"] == "abc"
        assert formatted["content"] == "hello world"
        assert formatted["score"] == 0.9
        # V1 should NOT have metadata field
        assert "metadata" not in formatted

    def test_format_search_result_dict(self):
        s = V1Strategy()
        r = {"id": "x", "content": "plain", "score": 0.5}
        formatted = s.format_search_result(r)
        assert formatted["id"] == "x"
        assert formatted["content"] == "plain"

    def test_build_context_with_results(self):
        s = V1Strategy()
        mgr = _make_mock_manager()
        mgr.search.return_value = [_make_mock_result("1", "test memory")]

        with patch("claw_mem.context_injection.format_memory_context", return_value="--- formatted ---"):
            result = s.build_context(mgr, {"topK": 5, "query": "test"})
            assert result["count"] == 1
            assert result["context"] == ["--- formatted ---"]

    def test_build_context_empty_results(self):
        s = V1Strategy()
        mgr = _make_mock_manager()
        mgr.search.return_value = []

        result = s.build_context(mgr, {"topK": 5, "query": "test"})
        assert result["count"] == 0
        assert result["context"] == []

    def test_build_context_exception(self):
        s = V1Strategy()
        mgr = MagicMock()
        mgr.search.side_effect = RuntimeError("search failed")
        result = s.build_context(mgr, {"query": "test"})
        assert result["context"] == []
        assert result["count"] == 0
        assert "error" in result

    def test_resolve_flush_plan_placeholder(self):
        s = V1Strategy()
        mgr = MagicMock()
        result = s.resolve_flush_plan(mgr, {})
        assert result["softThresholdTokens"] == 100000
        assert result["forceFlushTranscriptBytes"] == 500000
        assert result["reserveTokensFloor"] == 20000
        assert result["totalMemories"] == 0
        assert "relativePath" in result

    def test_resolve_flush_plan_exception(self):
        s = V1Strategy()
        mgr = MagicMock()
        mgr.get_stats.side_effect = RuntimeError("fail")
        result = s.resolve_flush_plan(mgr, {})
        # V1 placeholder doesn't call get_stats, so it should still succeed
        assert "softThresholdTokens" in result


# ---- OpenClawAdapter ---------------------------------------------------------

class TestOpenClawAdapter:
    @pytest.fixture
    def mgr(self):
        return _make_mock_manager()

    @pytest.fixture
    def strategy(self):
        return V2Strategy()

    @pytest.fixture
    def adapter(self, mgr, strategy):
        return OpenClawAdapter(mgr, strategy)

    def test_version_property(self, adapter):
        assert adapter.version == "2.8.0"

    def test_strategy_property(self, adapter, strategy):
        assert adapter.strategy is strategy

    def test_get_initialize_response(self, adapter):
        resp = adapter.get_initialize_response()
        assert resp["status"] == "ok"
        assert resp["version"] == "2.6.0"

    def test_search_returns_formatted_results(self, adapter, mgr):
        results = adapter.search({"query": "test", "topK": 3})
        assert len(results) == 2
        assert results[0]["id"] == "mem-1"
        assert results[0]["text"] == "Memory one content"
        assert results[0]["score"] == 0.95
        assert "metadata" in results[0]

    def test_search_cache_hit(self, adapter, mgr):
        adapter.search({"query": "test"})
        first_call_count = mgr.search.call_count
        # Same query should hit cache
        adapter.search({"query": "test"})
        assert mgr.search.call_count == first_call_count

    def test_search_cache_bust_different_query(self, adapter, mgr):
        adapter.search({"query": "test"})
        first_call_count = mgr.search.call_count
        adapter.search({"query": "different"})
        assert mgr.search.call_count > first_call_count

    def test_store_returns_id(self, adapter, mgr):
        result = adapter.store({"text": "new memory"})
        assert result["id"] == "new-id-1234"
        assert result["status"] == "stored"

    def test_store_invalidates_cache(self, adapter, mgr):
        adapter.search({"query": "test"})
        first_count = mgr.search.call_count
        adapter.store({"text": "write"})
        # Cache should be invalidated after store
        adapter.search({"query": "test"})
        assert mgr.search.call_count > first_count

    def test_get_found(self, adapter):
        result = adapter.get({"id": "mem-1"})
        assert result["id"] == "mem-1"
        assert result["text"] == "Memory one content"

    def test_get_not_found(self, adapter, mgr):
        mgr.get.return_value = None
        result = adapter.get({"id": "nonexistent"})
        assert result == {"error": "Memory not found"}

    def test_delete(self, adapter, mgr):
        result = adapter.delete({"id": "mem-1"})
        assert result["deleted"] is True
        mgr.delete.assert_called_once_with("mem-1")

    def test_ping(self, adapter):
        assert adapter.ping() == {"pong": True}

    def test_status(self, adapter):
        result = adapter.status()
        assert result["status"] == "ok"
        assert result["initialized"] is True
        assert "workspace" in result

    def test_start_session(self, adapter, mgr):
        result = adapter.start_session({"sessionId": "s1"})
        assert result["status"] == "started"
        assert result["sessionId"] == "s1"
        mgr.start_session.assert_called_once_with("s1")

    def test_start_session_default_id(self, adapter, mgr):
        result = adapter.start_session({})
        assert result["sessionId"] == "default"
        mgr.start_session.assert_called_once_with("default")

    def test_start_session_error(self, adapter, mgr):
        mgr.start_session.side_effect = RuntimeError("fail")
        result = adapter.start_session({})
        assert result["status"] == "error"
        assert "fail" in result["error"]

    def test_end_session(self, adapter, mgr):
        result = adapter.end_session({"sessionId": "s1"})
        assert result["status"] == "ended"
        mgr.end_session.assert_called_once()

    def test_end_session_error(self, adapter, mgr):
        mgr.end_session.side_effect = RuntimeError("fail")
        result = adapter.end_session({})
        assert result["status"] == "error"

    def test_sessions(self, adapter, mgr):
        mgr.sessions = ["s1", "s2"]
        result = adapter.sessions()
        assert result["sessions"] == ["s1", "s2"]

    def test_sessions_error(self, adapter, mgr):
        mgr.sessions = None
        result = adapter.sessions()
        assert result["sessions"] == []

    def test_build_context_delegates(self, adapter, strategy, mgr):
        with patch.object(strategy, "build_context", return_value={"context": [], "count": 0}) as mock_bc:
            adapter.build_context({"query": "test"})
            mock_bc.assert_called_once_with(mgr, {"query": "test"})

    def test_resolve_flush_plan_delegates(self, adapter, strategy, mgr):
        with patch.object(strategy, "resolve_flush_plan", return_value={"plan": True}) as mock_rfp:
            adapter.resolve_flush_plan({})
            mock_rfp.assert_called_once_with(mgr, {})


# ---- AdapterRegistry ---------------------------------------------------------

class TestAdapterRegistry:
    def test_detect_version_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("claw_mem.adapters.registry.Path.exists", return_value=False):
                key = AdapterRegistry.detect_version_key()
                assert key == "v2"

    def test_detect_version_from_env(self):
        with patch.dict(os.environ, {"OPENCLAW_VERSION": "1.5.0"}, clear=True):
            key = AdapterRegistry.detect_version_key()
            assert key == "v1"

    def test_detect_version_from_env_v2(self):
        with patch.dict(os.environ, {"OPENCLAW_VERSION": "2.9.0"}, clear=True):
            key = AdapterRegistry.detect_version_key()
            assert key == "v2"

    def test_detect_version_from_config(self):
        with patch.dict(os.environ, {}, clear=True):
            mock_open = mock.mock_open(read_data='{"version": "1"}')
            with patch("claw_mem.adapters.registry.Path.exists", return_value=True):
                with patch("builtins.open", mock_open):
                    key = AdapterRegistry.detect_version_key()
                    assert key == "v1"

    def test_create_strategy_v2(self):
        s = AdapterRegistry.create_strategy("v2")
        assert isinstance(s, V2Strategy)

    def test_create_strategy_v1(self):
        s = AdapterRegistry.create_strategy("v1")
        assert isinstance(s, V1Strategy)

    def test_create_strategy_unknown_raises(self):
        with pytest.raises(AdapterError, match="Unknown adapter version"):
            AdapterRegistry.create_strategy("v3")

    def test_create_strategy_with_default(self):
        with patch("claw_mem.adapters.registry.AdapterRegistry.detect_version_key", return_value="v2"):
            s = AdapterRegistry.create_strategy()
            assert isinstance(s, V2Strategy)

    def test_create_adapter(self):
        mgr = MagicMock()
        adapter = AdapterRegistry.create_adapter(mgr, "v2")
        assert isinstance(adapter, OpenClawAdapter)
        assert adapter.version == "2.8.0"

    def test_create_adapter_v1(self):
        mgr = MagicMock()
        adapter = AdapterRegistry.create_adapter(mgr, "v1")
        assert isinstance(adapter, OpenClawAdapter)
        assert adapter.version == "2.0.0"


# ---- Integration / Regression ------------------------------------------------

class TestIntegration:
    """End-to-end tests: bridge-like usage with mock manager."""

    def test_full_search_flow(self):
        mgr = _make_mock_manager()
        mgr.search.return_value = [
            _make_mock_result("a", "content A", score=0.9, metadata={"tag": "x"}),
            _make_mock_result("b", "content B", score=0.7, metadata={"tag": "y"}),
        ]
        adapter = AdapterRegistry.create_adapter(mgr, "v2")

        results = adapter.search({"query": "test", "topK": 10})
        assert len(results) == 2
        assert all("id" in r and "text" in r and "score" in r and "metadata" in r for r in results)

    def test_full_store_then_search(self):
        mgr = _make_mock_manager()
        adapter = AdapterRegistry.create_adapter(mgr, "v2")

        store_result = adapter.store({"text": "A new fact", "metadata": {"source": "chat"}})
        assert store_result["status"] == "stored"

        results = adapter.search({"query": "fact"})
        assert len(results) > 0

    def test_format_consistency_v2_vs_v1(self):
        raw = _make_mock_result("id1", "hello", score=0.95, metadata={"key": "value"})

        v2_format = V2Strategy().format_search_result(raw)
        v1_format = V1Strategy().format_search_result(raw)

        # Both have id and score
        assert v2_format["id"] == v1_format["id"]
        assert v2_format["score"] == v1_format["score"]
        # V2 uses "text", V1 uses "content"
        assert "text" in v2_format
        assert "content" in v1_format
        # V2 has metadata, V1 does not
        assert "metadata" in v2_format
        assert "metadata" not in v1_format

    def test_search_response_regression_v2(self):
        """Verify V2 search result format matches original bridge output."""
        mgr = _make_mock_manager()
        mgr.search.return_value = [
            _make_mock_result("abc123", "Test memory content", score=0.95, metadata={"tag": "test"})
        ]
        adapter = OpenClawAdapter(mgr, V2Strategy())

        results = adapter.search({"query": "test", "topK": 10, "memory_type": "episodic"})

        assert len(results) == 1
        r = results[0]
        assert r["id"] == "abc123"
        assert r["text"] == "Test memory content"
        assert r["score"] == 0.95
        assert r["metadata"] == {"tag": "test"}
