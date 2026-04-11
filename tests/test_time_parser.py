"""
Tests for TimeExpressionParser

Tests temporal expression parsing for memory retrieval.
"""

import pytest
from datetime import datetime, timedelta
from claw_mem.retrieval.time_parser import TimeExpressionParser


class TestTimeExpressionParser:
    """Test time expression parsing"""
    
    def setup_method(self):
        """Setup parser for each test"""
        self.parser = TimeExpressionParser()
    
    def test_is_time_query_positive(self):
        """Test detection of time-related queries"""
        # Note: The actual implementation may not have is_time_query method
        # Test the parse method instead
        result = self.parser.parse("What did the user do 3 days ago?")
        assert result is not None
        
        result = self.parser.parse("What happened yesterday?")
        assert result is not None
        
        result = self.parser.parse("What did the user mention last week?")
        assert result is not None
    
    def test_is_time_query_negative(self):
        """Test detection of non-time queries"""
        # Non-time queries should return None
        result = self.parser.parse("What is the user's favorite food?")
        assert result is None
        
        result = self.parser.parse("What is the user's job?")
        assert result is None
    
    def test_parse_days_ago(self):
        """Test parsing 'X days ago' expressions"""
        result = self.parser.parse("3 days ago")
        assert result is not None
        start_time, end_time = result
        
        # Should be approximately 3 days ago
        now = datetime.now()
        expected_start = now - timedelta(days=3)
        
        # Allow 1 hour tolerance
        diff = abs((start_time - expected_start).total_seconds())
        assert diff < 3600  # Within 1 hour
    
    def test_parse_yesterday(self):
        """Test parsing 'yesterday' expression"""
        result = self.parser.parse("yesterday")
        assert result is not None
        start_time, end_time = result
        
        now = datetime.now()
        expected_start = now - timedelta(days=1)
        
        diff = abs((start_time - expected_start).total_seconds())
        assert diff < 86400  # Within 1 day (yesterday is a full day)
    
    def test_parse_today(self):
        """Test parsing 'today' expression"""
        result = self.parser.parse("today")
        assert result is not None
        start_time, end_time = result
        
        now = datetime.now()
        
        # Today should start at midnight and end now
        assert start_time.date() == now.date()
        assert end_time >= start_time
    
    def test_parse_last_week(self):
        """Test parsing 'last week' expression"""
        result = self.parser.parse("last week")
        assert result is not None
        start_time, end_time = result
        
        now = datetime.now()
        expected_start = now - timedelta(weeks=1)
        
        diff = abs((start_time - expected_start).total_seconds())
        assert diff < 86400  # Within 1 day
    
    def test_parse_last_month(self):
        """Test parsing 'last month' expression"""
        result = self.parser.parse("last month")
        assert result is not None
        start_time, end_time = result
        
        # Should be approximately 30 days ago
        now = datetime.now()
        expected_start = now - timedelta(days=30)
        
        diff = abs((start_time - expected_start).total_seconds())
        assert diff < 86400  # Within 1 day
    
    def test_parse_invalid_expression(self):
        """Test parsing invalid expression returns None"""
        assert self.parser.parse("favorite food") is None
        assert self.parser.parse("user's name") is None
    
    def test_parse_recently(self):
        """Test parsing 'recently' expression"""
        result = self.parser.parse("What happened recently?")
        assert result is not None
        start_time, end_time = result
        
        # Recently should be within the last few days
        now = datetime.now()
        assert end_time <= now
        assert start_time < end_time
    
    def test_relative_time_patterns(self):
        """Test various relative time patterns"""
        patterns = [
            "2 days ago",
            "5 days ago",
            "1 week ago",
            "2 weeks ago",
            "1 month ago",
        ]
        
        for pattern in patterns:
            result = self.parser.parse(pattern)
            assert result is not None, f"Failed to parse: {pattern}"
    
    def test_context_in_query(self):
        """Test parsing time expression within larger query"""
        result = self.parser.parse("What did the user do 3 days ago about the project?")
        assert result is not None
        
        result = self.parser.parse("When did the user mention vacation last week?")
        assert result is not None

    def test_extract_time_value_relative(self):
        """Test extract_time_value with relative time"""
        result = self.parser.extract_time_value("What happened 3 days ago?")
        assert result is not None
        assert "3" in result or "days" in result
        
        result = self.parser.extract_time_value("Records from 2 weeks ago")
        assert result is not None
    
    def test_extract_time_value_specific(self):
        """Test extract_time_value with specific time"""
        result = self.parser.extract_time_value("What happened yesterday?")
        assert result is not None
        assert "yesterday" in result.lower()
        
        result = self.parser.extract_time_value("Today's activities")
        assert result is not None
        assert "today" in result.lower()
    
    def test_extract_time_value_none(self):
        """Test extract_time_value with no time expression"""
        result = self.parser.extract_time_value("What is your favorite food?")
        assert result is None
        
        result = self.parser.extract_time_value("User's job")
        assert result is None
    
    def test_is_time_query_true(self):
        """Test is_time_query returns True for time queries"""
        assert self.parser.is_time_query("When did you do this?")
        assert self.parser.is_time_query("What happened last week?")
        assert self.parser.is_time_query("What did you do 3 days ago?")
        assert self.parser.is_time_query("Recently mentioned items")
        assert self.parser.is_time_query("Activities from yesterday")
    
    def test_is_time_query_false(self):
        """Test is_time_query returns False for non-time queries"""
        assert not self.parser.is_time_query("What is your name?")
        assert not self.parser.is_time_query("Favorite foods")
        assert not self.parser.is_time_query("Programming languages")
    
    def test_filter_memories_by_time(self):
        """Test filtering memories by time range"""
        now = datetime.now()
        
        # Create test memories
        memories = [
            {
                "id": "1",
                "content": "Recent memory",
                "timestamp": (now - timedelta(hours=2)).isoformat()
            },
            {
                "id": "2",
                "content": "Old memory",
                "timestamp": (now - timedelta(days=5)).isoformat()
            },
            {
                "id": "3",
                "content": "Very old memory",
                "timestamp": (now - timedelta(days=30)).isoformat()
            },
        ]
        
        # Filter for last 3 days
        start_time = now - timedelta(days=3)
        end_time = now
        
        filtered = self.parser.filter_memories_by_time(memories, start_time, end_time)
        
        # Should only include recent memory
        assert len(filtered) == 1
        assert filtered[0]["id"] == "1"
    
    def test_filter_memories_no_timestamp(self):
        """Test filtering memories without timestamps"""
        memories = [
            {"id": "1", "content": "No timestamp"},
            {"id": "2", "content": "Also no timestamp"},
        ]
        
        now = datetime.now()
        filtered = self.parser.filter_memories_by_time(
            memories,
            now - timedelta(days=1),
            now
        )
        
        # Should return empty list
        assert len(filtered) == 0
    
    def test_filter_memories_invalid_timestamp(self):
        """Test filtering memories with invalid timestamps"""
        memories = [
            {"id": "1", "content": "Invalid timestamp", "timestamp": "invalid"},
            {"id": "2", "content": "Null timestamp", "timestamp": None},
        ]
        
        now = datetime.now()
        filtered = self.parser.filter_memories_by_time(
            memories,
            now - timedelta(days=1),
            now
        )
        
        # Should return empty list (skipping invalid timestamps)
        assert len(filtered) == 0
    
    def test_filter_memories_datetime_object(self):
        """Test filtering with datetime objects instead of strings"""
        now = datetime.now()
        
        memories = [
            {
                "id": "1",
                "content": "Memory with datetime object",
                "timestamp": now - timedelta(hours=1)
            },
        ]
        
        filtered = self.parser.filter_memories_by_time(
            memories,
            now - timedelta(days=1),
            now
        )
        
        # Should include memory
        assert len(filtered) == 1
        assert filtered[0]["id"] == "1"
