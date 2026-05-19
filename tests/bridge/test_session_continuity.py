"""Unit tests for session continuity bridge methods (v2.13.x + v3.0.0)."""

import pytest

pytestmark = pytest.mark.skip(reason="Bridge dependency issues — fix in rc.15")
from claw_mem.bridge import ClawMemBridge
from claw_mem.classifier import detect_content_type, classify_content


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
    """Use classifier module directly (v3.0.0: _detect_content_type moved to classifier)."""

    def test_detect_decision(self):
        r = detect_content_type("我们选择使用 Python")
        assert r["type"] == "decision"
        assert r["importance"] == 0.9

    def test_detect_decision_en(self):
        r = detect_content_type("let's use FastAPI")
        assert r["type"] == "decision"
        assert r["importance"] == 0.9

    def test_detect_preference(self):
        r = detect_content_type("我喜欢简洁的回复")
        assert r["type"] == "preference"
        assert r["importance"] == 0.8

    def test_detect_preference_en(self):
        r = detect_content_type("I prefer short answers")
        assert r["type"] == "preference"
        assert r["importance"] == 0.8

    def test_detect_task_context(self):
        r = detect_content_type("我们在构建 v4.0.0")
        assert r["type"] == "task_context"
        assert r["importance"] == 0.7

    def test_detect_task_context_en(self):
        r = detect_content_type("we're building the plugin migration")
        assert r["type"] == "task_context"
        assert r["importance"] == 0.7

    def test_detect_fact(self):
        r = detect_content_type("这是一个重要的教训")
        assert r["type"] == "fact"
        assert r["importance"] == 0.6

    def test_ignore_casual_chat(self):
        r = detect_content_type("hello how are you")
        assert r["type"] == "chat"
        assert r["importance"] < 0.5

    def test_ignore_short_message(self):
        r = detect_content_type("ok")
        assert r["type"] == "chat"
        assert r["importance"] < 0.3


class TestExtractImportantContent:
    def test_extract_all_important(self, bridge, sample_messages):
        r = bridge._handle_extract_important_content({"messages": sample_messages})
        assert r["count"] >= 4
        types = {item["type"] for item in r["important"]}
        assert "decision" in types
        assert "preference" in types
        assert "task_context" in types

    def test_extract_empty(self, bridge):
        r = bridge._handle_extract_important_content({"messages": []})
        assert r["count"] == 0
        assert r["important"] == []

    def test_extract_single_message(self, bridge):
        r = bridge._handle_extract_important_content(
            {"messages": [{"role": "user", "content": "I prefer Chinese"}]}
        )
        assert r["count"] >= 1

    def test_skip_short_messages(self, bridge):
        r = bridge._handle_extract_important_content(
            {"messages": [{"role": "user", "content": "hi"}]}
        )
        assert r["count"] == 0


class TestGenerateSessionSummary:
    def test_generate_summary(self, bridge, sample_messages):
        r = bridge._handle_generate_session_summary({"messages": sample_messages})
        assert "summary" in r
        assert "overview" in r["summary"]
        assert "decisions" in r["summary"]
        assert len(r["summary"]["preferences"]) >= 1

    def test_empty_summary(self, bridge):
        r = bridge._handle_generate_session_summary({"messages": []})
        assert r["summary"]["decisions"] == []
        assert r["summary"]["important_count"] == 0

    def test_summary_with_important(self, bridge, sample_messages):
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
