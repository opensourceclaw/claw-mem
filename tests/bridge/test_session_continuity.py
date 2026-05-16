"""Unit tests for session continuity bridge methods (v2.13.x)."""

import pytest
from claw_mem.bridge import ClawMemBridge


@pytest.fixture
def bridge():
    return ClawMemBridge()


@pytest.fixture
def sample_messages():
    return [
        {"role": "user", "content": "我们选择使用 Python 作为主要语言"},
        {"role": "assistant", "content": "好的，let's use FastAPI as the web framework."},
        {"role": "user", "content": "hi"},
        {"role": "user", "content": "我喜欢简洁的回复风格"},
        {"role": "assistant", "content": "明白，以后注意简洁。"},
        {"role": "user", "content": "我们在构建 neoclaw v4.0.0"},
        {"role": "user", "content": "这个很重要，请记住"},
        {"role": "assistant", "content": "ok"},
    ]


class TestDetectContentType:
    def test_detect_decision(self, bridge):
        r = bridge._detect_content_type("我们选择使用 Python")
        assert r["type"] == "decision"
        assert r["importance"] == 0.9

    def test_detect_decision_en(self, bridge):
        r = bridge._detect_content_type("let's use FastAPI")
        assert r["type"] == "decision"
        assert r["importance"] == 0.9

    def test_detect_preference(self, bridge):
        r = bridge._detect_content_type("我喜欢简洁的回复")
        assert r["type"] == "preference"
        assert r["importance"] == 0.8

    def test_detect_preference_en(self, bridge):
        r = bridge._detect_content_type("I prefer short answers")
        assert r["type"] == "preference"
        assert r["importance"] == 0.8

    def test_detect_task_context(self, bridge):
        r = bridge._detect_content_type("我们在构建 v4.0.0")
        assert r["type"] == "task_context"
        assert r["importance"] == 0.7

    def test_detect_task_context_en(self, bridge):
        r = bridge._detect_content_type("we're building the plugin migration")
        assert r["type"] == "task_context"
        assert r["importance"] == 0.7

    def test_detect_fact(self, bridge):
        r = bridge._detect_content_type("这是一个重要的教训")
        assert r["type"] == "fact"
        assert r["importance"] == 0.6

    def test_ignore_casual_chat(self, bridge):
        r = bridge._detect_content_type("hello how are you")
        assert r["type"] == "chat"
        assert r["importance"] < 0.5

    def test_ignore_short_message(self, bridge):
        r = bridge._detect_content_type("ok")
        assert r["type"] == "chat"
        assert r["importance"] < 0.3


class TestExtractImportantContent:
    def test_extract_all_important(self, bridge, sample_messages):
        r = bridge._handle_extract_important_content({"messages": sample_messages})
        assert r["count"] >= 4
        types = {item["type"] for item in r["important"]}
        assert "decision" in types
        assert "preference" in types

    def test_include_source(self, bridge, sample_messages):
        r = bridge._handle_extract_important_content({"messages": sample_messages})
        sources = {item["source"] for item in r["important"]}
        assert "user" in sources

    def test_include_importance(self, bridge, sample_messages):
        r = bridge._handle_extract_important_content({"messages": sample_messages})
        for item in r["important"]:
            assert "importance" in item
            assert 0.0 <= item["importance"] <= 1.0

    def test_bypass_short_messages(self, bridge):
        r = bridge._handle_extract_important_content({
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "user", "content": "ok"},
                {"role": "assistant", "content": "yes"},
            ]
        })
        assert r["count"] == 0

    def test_empty_messages(self, bridge):
        r = bridge._handle_extract_important_content({"messages": []})
        assert r["count"] == 0

    def test_none_messages(self, bridge):
        r = bridge._handle_extract_important_content({"messages": None})
        assert r["count"] == 0


class TestGenerateSessionSummary:
    def test_generate_overview(self, bridge, sample_messages):
        r = bridge._handle_generate_session_summary({"messages": sample_messages})
        assert r["summary"]["overview"]
        assert len(r["summary"]["overview"]) > 0

    def test_extract_decisions(self, bridge, sample_messages):
        r = bridge._handle_generate_session_summary({"messages": sample_messages})
        decisions = r["summary"]["decisions"]
        assert len(decisions) >= 1
        assert any("Python" in d or "FastAPI" in d for d in decisions)

    def test_extract_preferences(self, bridge, sample_messages):
        r = bridge._handle_generate_session_summary({"messages": sample_messages})
        prefs = r["summary"]["preferences"]
        assert len(prefs) >= 1
        assert any("简洁" in p for p in prefs)

    def test_empty_session(self, bridge):
        r = bridge._handle_generate_session_summary({"messages": []})
        assert r["summary"]["total_messages"] == 0
        assert r["summary"]["important_count"] == 0

    def test_total_messages_count(self, bridge, sample_messages):
        r = bridge._handle_generate_session_summary({"messages": sample_messages})
        assert r["summary"]["total_messages"] == len(sample_messages)

    def test_important_count(self, bridge, sample_messages):
        r = bridge._handle_generate_session_summary({"messages": sample_messages})
        assert r["summary"]["important_count"] > 0


class TestHandleDetectContentType:
    def test_rpc_handler(self, bridge):
        r = bridge._handle_detect_content_type({"content": "我们决定用 FastAPI"})
        assert r["type"] == "decision"

    def test_empty_content(self, bridge):
        r = bridge._handle_detect_content_type({"content": ""})
        assert r["type"] == "chat"
        assert r["importance"] == 0.0
