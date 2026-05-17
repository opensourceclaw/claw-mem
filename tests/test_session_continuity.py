"""Tests for session continuity features (Phase 1 - Critical Fixes, v2.13.x).

Tests cover:
  - Content classifier (decision, preference, task_context, fact, chat)
  - extract_important_content bridge method
  - generate_session_summary bridge method
  - detect_content_type bridge method
"""

import pytest
from claw_mem.classifier import (
    classify_content,
    ContentClassification,
    extract_important_content,
    generate_session_summary,
    detect_content_type,
    DETECTION_RULES,
    ContentType,
)


# ============================================================================
# content_classify tests
# ============================================================================

class TestContentClassifier:
    """Tests for classify_content() function."""

    def test_classify_decision_en(self):
        """Should detect decision statements in English."""
        result = classify_content("Let's use Python 3.10 for this project.")
        assert result.type == 'decision'
        assert result.importance == 0.9
        assert result.should_save is True

    def test_classify_decision_zh(self):
        """Should detect decision statements in Chinese."""
        result = classify_content("我们决定使用PostgreSQL数据库。")
        assert result.type == 'decision'
        assert result.importance >= 0.8
        assert result.should_save is True

    def test_classify_preference_en(self):
        """Should detect user preferences in English."""
        result = classify_content("I prefer Chinese for all responses.")
        assert result.type == 'preference'
        assert result.importance == 0.8
        assert result.should_save is True

    def test_classify_preference_zh(self):
        """Should detect user preferences in Chinese."""
        result = classify_content("我喜欢简洁的回答方式。")
        assert result.type == 'preference'
        assert result.importance >= 0.7
        assert result.should_save is True

    def test_classify_task_context_en(self):
        """Should detect task context in English."""
        result = classify_content("We're building a REST API for user management.")
        assert result.type == 'task_context'
        assert result.importance == 0.7
        assert result.should_save is True

    def test_classify_task_context_zh(self):
        """Should detect task context in Chinese."""
        result = classify_content("我们在开发一个会话连续性修复功能。")
        assert result.type == 'task_context'
        assert result.importance == 0.7
        assert result.should_save is True

    def test_classify_fact_en(self):
        """Should detect important facts in English."""
        result = classify_content("Important: the API key expires on May 30.")
        assert result.type == 'fact'
        assert result.importance == 0.6
        assert result.should_save is True

    def test_classify_fact_zh(self):
        """Should detect important facts in Chinese."""
        result = classify_content("记住：生产环境数据库地址是 prod-db.example.com")
        assert result.type == 'fact'
        assert result.importance >= 0.5
        assert result.should_save is True

    def test_classify_casual_chat(self):
        """Should classify casual chat with low importance."""
        result = classify_content("Hello, how are you?")
        assert result.type == 'chat'
        assert result.importance < 0.5
        assert result.should_save is False

    def test_classify_short_message(self):
        """Should classify very short messages as chat."""
        result = classify_content("OK")
        assert result.type == 'chat'
        assert result.should_save is False

    def test_classify_empty_content(self):
        """Should handle empty content."""
        result = classify_content("")
        assert result.type == 'chat'
        assert result.importance == 0.0

    def test_classify_none_content(self):
        """Should handle None content."""
        result = classify_content(None)
        assert result.type == 'chat'
        assert result.importance == 0.0

    def test_classify_mixed_content_decision_first(self):
        """Should detect decision even in mixed content (higher priority)."""
        result = classify_content("I've decided to use PostgreSQL. Let me know if you prefer something else.")
        assert result.type == 'decision'
        assert result.should_save is True

    def test_classify_importance_range(self):
        """Importance scores should be in range [0.0, 1.0]."""
        tests = [
            "Let's use Python.",
            "I prefer dark mode.",
            "We're building a new feature.",
            "Hello there.",
            "",
        ]
        for content in tests:
            result = classify_content(content)
            assert 0.0 <= result.importance <= 1.0, \
                f"Importance {result.importance} out of range for: {content}"

    def test_classify_reasoning_field(self):
        """Should include reasoning in classification result."""
        result = classify_content("Let's use FastAPI.")
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    def test_detection_rules_structure(self):
        """DETECTION_RULES should have all expected types with keywords and importance."""
        expected_types = ['decision', 'preference', 'task_context', 'fact', 'chat']
        for t in expected_types:
            assert t in DETECTION_RULES
            assert 'keywords' in DETECTION_RULES[t]
            assert 'importance' in DETECTION_RULES[t]
            assert 0.0 <= DETECTION_RULES[t]['importance'] <= 1.0


# ============================================================================
# extract_important_content tests
# ============================================================================

class TestExtractImportantContent:
    """Tests for extract_important_content() function."""

    def test_extract_decision_from_assistant(self):
        """Should extract decision statements from assistant messages."""
        messages = [
            {"role": "assistant", "content": "Let's use Python 3.10 for this project."}
        ]
        result = extract_important_content(messages)
        assert result["count"] >= 1
        assert any(i["type"] == "decision" for i in result["important"])

    def test_extract_preference_from_user(self):
        """Should extract user preferences."""
        messages = [
            {"role": "user", "content": "I prefer Chinese for all responses."}
        ]
        result = extract_important_content(messages)
        assert result["count"] >= 1
        assert any(i["type"] == "preference" for i in result["important"])

    def test_extract_task_context(self):
        """Should extract task context."""
        messages = [
            {"role": "user", "content": "We're building a REST API for user management."}
        ]
        result = extract_important_content(messages)
        assert result["count"] >= 1
        assert any(i["type"] == "task_context" for i in result["important"])

    def test_ignore_casual_chat(self):
        """Should ignore casual conversation."""
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks for asking!"}
        ]
        result = extract_important_content(messages)
        for item in result["important"]:
            assert item["importance"] < 0.5

    def test_extract_all_user_messages(self):
        """Should extract all important user messages (not just last 5)."""
        messages = []
        for i in range(15):
            if i % 3 == 0:
                content = f"I prefer option {i} for the configuration."
            elif i % 3 == 1:
                content = f"Let's use framework version {i}."
            else:
                content = f"We're building component {i} of the system."
            messages.append({"role": "user", "content": content})

        result = extract_important_content(messages)
        # All 15 messages should be captured as important
        assert result["count"] >= 15, f"Expected >=15, got {result['count']}"

    def test_include_source_information(self):
        """Should include source (user/assistant) in results."""
        messages = [
            {"role": "user", "content": "I prefer dark mode."},
            {"role": "assistant", "content": "I'll use dark theme for code."}
        ]
        result = extract_important_content(messages)
        for item in result["important"]:
            assert "source" in item
            assert item["source"] in ["user", "assistant", "system"]

    def test_include_importance_scores(self):
        """Should include importance score for each item."""
        messages = [
            {"role": "assistant", "content": "Let's use Python 3.10."}
        ]
        result = extract_important_content(messages)
        for item in result["important"]:
            assert "importance" in item
            assert 0.0 <= item["importance"] <= 1.0

    def test_empty_messages(self):
        """Should handle empty message list."""
        result = extract_important_content([])
        assert result["count"] == 0
        assert result["important"] == []

    def test_none_messages(self):
        """Should handle None messages."""
        result = extract_important_content(None)
        assert result["count"] == 0
        assert result["important"] == []

    def test_non_list_messages(self):
        """Should handle non-list messages parameter."""
        result = extract_important_content("not a list")
        assert result["count"] == 0
        assert result["important"] == []

    def test_skip_short_messages(self):
        """Should skip messages shorter than 10 characters."""
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "user", "content": "I prefer Chinese for responses."},
        ]
        result = extract_important_content(messages)
        # "Hi" should be skipped
        items = [i["content"] for i in result["important"]]
        assert all(len(content) >= 10 for content in items)

    def test_extract_all_important_types(self):
        """Should extract multiple types from multi-turn conversation."""
        messages = [
            {"role": "user", "content": "I prefer Chinese."},
            {"role": "assistant", "content": "Understood, let's use Chinese."},
            {"role": "user", "content": "We're building a REST API for this task."},
            {"role": "assistant", "content": "We'll use FastAPI for that."},
            {"role": "user", "content": "Important: remember to use PostgreSQL."},
            {"role": "user", "content": "Hello there."},
        ]
        result = extract_important_content(messages)
        assert result["count"] >= 4  # preference + decision + task + fact
        types = [i["type"] for i in result["important"]]
        assert "preference" in types
        assert "task_context" in types
        assert "decision" in types
        assert "fact" in types

    def test_include_content_field(self):
        """Each result should include the original content."""
        messages = [
            {"role": "user", "content": "I prefer Chinese for all responses."},
        ]
        result = extract_important_content(messages)
        for item in result["important"]:
            assert "content" in item
            assert isinstance(item["content"], str)

    def test_extract_from_system_role(self):
        """Should extract content from system messages too."""
        messages = [
            {"role": "system", "content": "Important system configuration: use Python 3.10"},
        ]
        result = extract_important_content(messages)
        assert result["count"] >= 1


# ============================================================================
# generate_session_summary tests
# ============================================================================

class TestSessionSummary:
    """Tests for generate_session_summary() function."""

    def test_generate_overview(self):
        """Should generate a session overview."""
        messages = [
            {"role": "user", "content": "Help me build a REST API."},
            {"role": "assistant", "content": "Sure, let's use FastAPI."},
            {"role": "user", "content": "I prefer PostgreSQL."},
        ]
        result = generate_session_summary(messages)
        summary = result["summary"]
        assert "overview" in summary
        assert len(summary["overview"]) > 0

    def test_extract_decisions_in_summary(self):
        """Should extract decisions from multi-message session."""
        messages = [
            {"role": "assistant", "content": "We'll use FastAPI for the backend."},
            {"role": "assistant", "content": "We'll go with PostgreSQL for the database."},
        ]
        result = generate_session_summary(messages)
        decisions = result["summary"]["decisions"]
        assert len(decisions) >= 2
        assert any("FastAPI" in d for d in decisions)

    def test_extract_preferences_in_summary(self):
        """Should extract preferences from session."""
        messages = [
            {"role": "user", "content": "I prefer Chinese responses."},
            {"role": "user", "content": "I like concise answers."},
        ]
        result = generate_session_summary(messages)
        prefs = result["summary"]["preferences"]
        assert len(prefs) >= 2

    def test_extract_tasks_in_summary(self):
        """Should extract tasks from session."""
        messages = [
            {"role": "user", "content": "I'm working on a REST API."},
        ]
        result = generate_session_summary(messages)
        tasks = result["summary"]["tasks"]
        assert len(tasks) >= 1

    def test_empty_session_summary(self):
        """Should handle empty session gracefully."""
        result = generate_session_summary([])
        assert result["summary"]["decisions"] == []
        assert result["summary"]["preferences"] == []
        assert result["summary"]["tasks"] == []
        assert result["summary"]["facts"] == []

    def test_summary_has_all_fields(self):
        """Summary should contain all required fields."""
        messages = [
            {"role": "user", "content": "I prefer Chinese."},
            {"role": "assistant", "content": "Let's use FastAPI."},
        ]
        result = generate_session_summary(messages)
        summary = result["summary"]
        required_fields = [
            "overview", "decisions", "preferences",
            "tasks", "facts", "total_messages", "important_count",
        ]
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"

    def test_total_messages_in_summary(self):
        """Total messages count should be included in summary."""
        messages = [
            {"role": "user", "content": "I prefer Chinese for all responses."},
            {"role": "assistant", "content": "I'll use Chinese from now on."},
            {"role": "user", "content": "Hello."},
        ]
        result = generate_session_summary(messages)
        assert result["summary"]["total_messages"] == 3


# ============================================================================
# detect_content_type tests
# ============================================================================

class TestDetectContentType:
    """Tests for detect_content_type() function."""

    def test_detect_decision(self):
        result = detect_content_type("Let's use Python 3.10.")
        assert result["type"] == "decision"
        assert result["importance"] >= 0.8

    def test_detect_preference(self):
        result = detect_content_type("I prefer dark mode.")
        assert result["type"] == "preference"
        assert result["importance"] >= 0.7

    def test_detect_chat(self):
        result = detect_content_type("Hello, how are you doing today?")
        assert result["type"] == "chat"
        assert result["importance"] < 0.5

    def test_detect_empty(self):
        result = detect_content_type("")
        assert result["type"] == "chat"
        assert result["importance"] == 0.0

    def test_detect_returns_dict_with_required_keys(self):
        result = detect_content_type("I decided to use Redis for caching.")
        assert "type" in result
        assert "importance" in result


# ============================================================================
# ContentClassification dataclass tests
# ============================================================================

class TestContentClassificationDataclass:
    """Tests for ContentClassification dataclass."""

    def test_create_instance(self):
        result = ContentClassification(
            type='decision',
            importance=0.9,
            should_save=True,
            reasoning="Matched keyword: 'use'",
        )
        assert result.type == 'decision'
        assert result.importance == 0.9
        assert result.should_save is True
        assert result.reasoning == "Matched keyword: 'use'"

    def test_default_fields(self):
        result = ContentClassification(
            type='chat',
            importance=0.3,
            should_save=False,
            reasoning="Default",
        )
        assert result.type == 'chat'
        assert result.importance == 0.3
        assert result.should_save is False

    def test_type_hint_literal(self):
        """ContentType should be a valid Literal type."""
        valid_types = {'decision', 'preference', 'task_context', 'fact', 'chat'}
        assert ContentType is not None
        # Verify valid types are accepted by the dataclass
        for t in valid_types:
            result = ContentClassification(
                type=t,
                importance=0.5,
                should_save=True,
                reasoning="test",
            )
            assert result.type == t


# ============================================================================
# Integration: classifier module with bridge pattern tests
# ============================================================================

class TestClassifierBridgeIntegration:
    """Tests mimicking the bridge.py handler pattern."""

    def test_detect_content_type_bridge_pattern(self):
        """Should work with the same pattern as bridge._handle_detect_content_type."""
        def handle_detect(params):
            content = params.get("content", "")
            if not content:
                return {"type": "chat", "importance": 0.0}
            return detect_content_type(str(content))

        result = handle_detect({"content": "Let's use FastAPI."})
        assert result["type"] == "decision"
        assert result["importance"] >= 0.8

    def test_extract_important_bridge_pattern(self):
        """Should work with the same pattern as bridge._handle_extract_important_content."""
        def handle_extract(params):
            return extract_important_content(params.get("messages", []))

        result = handle_extract({
            "messages": [
                {"role": "user", "content": "I prefer Chinese for all responses."},
                {"role": "assistant", "content": "Let's use Python 3.10 for the project."},
            ]
        })
        assert result["count"] >= 2
        types = [i["type"] for i in result["important"]]
        assert "preference" in types
        assert "decision" in types

    def test_generate_summary_bridge_pattern(self):
        """Should work with the same pattern as bridge._handle_generate_session_summary."""
        def handle_summary(params):
            return generate_session_summary(params.get("messages", []))

        result = handle_summary({
            "messages": [
                {"role": "user", "content": "I prefer Chinese for responses."},
                {"role": "assistant", "content": "We'll use FastAPI for the backend."},
                {"role": "user", "content": "Good, let's also use PostgreSQL."},
            ]
        })
        assert len(result["summary"]["decisions"]) >= 1
        assert len(result["summary"]["preferences"]) >= 1
