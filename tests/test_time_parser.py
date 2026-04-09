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
