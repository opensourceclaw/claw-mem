#!/usr/bin/env python3
"""
Tests for FeedbackHandler
"""

import pytest
from claw_mem.values import (
    FeedbackHandler,
    ValueSuggestion,
    FeedbackStatus,
)


class TestValueSuggestion:
    """Test ValueSuggestion"""

    def test_creation(self):
        """Test suggestion creation"""
        suggestion = ValueSuggestion(
            id="test-1",
            user_id="user1",
            suggestion_type="principle",
            content="Be honest"
        )

        assert suggestion.id == "test-1"
        assert suggestion.status == FeedbackStatus.PENDING


class TestFeedbackHandler:
    """Test FeedbackHandler"""

    @pytest.fixture
    def handler(self):
        """Create handler"""
        return FeedbackHandler()

    def test_creation(self, handler):
        """Test creation"""
        assert handler.value_store is not None

    def test_request_confirmation(self, handler):
        """Test request confirmation"""
        suggestion = handler.request_confirmation(
            user_id="user1",
            value_type="principle",
            content="Be honest",
            evidence=["feedback1"]
        )

        assert suggestion is not None
        assert suggestion.user_id == "user1"
        assert suggestion.suggestion_type == "principle"
        assert suggestion.status == FeedbackStatus.PENDING

    def test_process_feedback_accept(self, handler):
        """Test process accepted feedback"""
        suggestion = handler.request_confirmation(
            user_id="user1",
            value_type="principle",
            content="Test principle"
        )

        result = handler.process_feedback(suggestion.id, accepted=True)

        assert result is True
        assert suggestion.status == FeedbackStatus.ACCEPTED

    def test_process_feedback_reject(self, handler):
        """Test process rejected feedback"""
        suggestion = handler.request_confirmation(
            user_id="user1",
            value_type="principle",
            content="Test principle"
        )

        result = handler.process_feedback(suggestion.id, accepted=False)

        assert result is True
        assert suggestion.status == FeedbackStatus.REJECTED

    def test_get_pending_suggestions(self, handler):
        """Test get pending suggestions"""
        handler.request_confirmation("user1", "principle", "p1")
        handler.request_confirmation("user1", "principle", "p2")

        pending = handler.get_pending_suggestions("user1")

        assert len(pending) == 2

    def test_get_accepted_suggestions(self, handler):
        """Test get accepted suggestions"""
        suggestion = handler.request_confirmation("user1", "principle", "p1")
        handler.process_feedback(suggestion.id, accepted=True)

        accepted = handler.get_accepted_suggestions("user1")

        assert len(accepted) >= 1

    def test_get_rejected_suggestions(self, handler):
        """Test get rejected suggestions"""
        suggestion = handler.request_confirmation("user1", "principle", "p1")
        handler.process_feedback(suggestion.id, accepted=False)

        rejected = handler.get_rejected_suggestions("user1")

        assert len(rejected) >= 1

    def test_process_invalid_suggestion(self, handler):
        """Test process invalid suggestion"""
        result = handler.process_feedback("invalid-id", accepted=True)

        assert result is False

    def test_suggest_update(self, handler):
        """Test suggest update"""
        suggestion_data = {
            "user_id": "user1",
            "type": "red_line",
            "content": "No violence",
            "evidence": ["evidence1"]
        }

        suggestion = handler.suggest_update(suggestion_data)

        assert suggestion.user_id == "user1"
        assert suggestion.suggestion_type == "red_line"
