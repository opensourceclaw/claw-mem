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
Time Expression Parser

Parses time expressions from natural language queries.
Part of the temporal reasoning enhancement for claw-mem.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict


class TimeExpressionParser:
    """
    Time Expression Parser
    
    Parses natural language time expressions and converts them to datetime filters.
    """
    
    def __init__(self):
        """Initialize time expression parser."""
        # Time expression patterns
        self.patterns = [
            # Relative time: "X days ago", "X weeks ago", etc.
            (r'(\d+)\s+(day|days|week|weeks|month|months|year|years)\s+ago', self._parse_relative_time),
            
            # Specific time: "yesterday", "today", "last week"
            (r'\b(yesterday|today|last\s+week|last\s+month|last\s+year)\b', self._parse_specific_time),
            
            # Time with context: "X days ago", "recently", "lately"
            (r'\b(recently|lately)\b', self._parse_recently),
        ]
    
    def parse(self, query: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parse time expression from query.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (start_time, end_time) if time expression found, None otherwise
        """
        query_lower = query.lower()
        
        for pattern, parser_func in self.patterns:
            match = re.search(pattern, query_lower)
            if match:
                return parser_func(match, query_lower)
        
        return None
    
    def _parse_relative_time(self, match, query: str) -> Tuple[datetime, datetime]:
        """
        Parse relative time expression.
        
        Examples:
            "3 days ago" → (3 days ago, now)
            "2 weeks ago" → (2 weeks ago, now)
        """
        number = int(match.group(1))
        unit = match.group(2).lower()
        
        now = datetime.now()
        
        if 'day' in unit:
            delta = timedelta(days=number)
        elif 'week' in unit:
            delta = timedelta(weeks=number)
        elif 'month' in unit:
            delta = timedelta(days=number * 30)  # Approximate
        elif 'year' in unit:
            delta = timedelta(days=number * 365)  # Approximate
        else:
            delta = timedelta(days=number)
        
        start_time = now - delta
        end_time = now
        
        return (start_time, end_time)
    
    def _parse_specific_time(self, match, query: str) -> Tuple[datetime, datetime]:
        """
        Parse specific time expression.
        
        Examples:
            "yesterday" → (yesterday 00:00, yesterday 23:59)
            "today" → (today 00:00, now)
            "last week" → (7 days ago, now)
        """
        now = datetime.now()
        expression = match.group(1).lower()
        
        if expression == 'yesterday':
            yesterday = now - timedelta(days=1)
            start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif expression == 'today':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif 'last week' in expression:
            start_time = now - timedelta(weeks=1)
            end_time = now
        elif 'last month' in expression:
            start_time = now - timedelta(days=30)
            end_time = now
        elif 'last year' in expression:
            start_time = now - timedelta(days=365)
            end_time = now
        else:
            # Default: last 24 hours
            start_time = now - timedelta(days=1)
            end_time = now
        
        return (start_time, end_time)
    
    def _parse_recently(self, match, query: str) -> Tuple[datetime, datetime]:
        """
        Parse "recently" or "lately" expression.
        
        Default: last 7 days
        """
        now = datetime.now()
        start_time = now - timedelta(days=7)
        end_time = now
        
        return (start_time, end_time)
    
    def extract_time_value(self, text: str) -> Optional[str]:
        """
        Extract time value from text (e.g., "3 days ago").
        
        Args:
            text: Text containing time expression
            
        Returns:
            Time expression string if found, None otherwise
        """
        # Pattern for "X days ago", "X weeks ago", etc.
        match = re.search(r'(\d+\s+(?:day|week|month|year)s?\s+ago)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern for "yesterday", "today", "last week"
        match = re.search(r'\b(yesterday|today|last\s+week|last\s+month|last\s+year)\b', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    def filter_memories_by_time(self, memories: List[Dict], start_time: datetime, 
                                 end_time: datetime) -> List[Dict]:
        """
        Filter memories by time range.
        
        Args:
            memories: List of memory records
            start_time: Start time
            end_time: End time
            
        Returns:
            Filtered memories
        """
        filtered = []
        
        for memory in memories:
            # Get timestamp from memory
            timestamp_str = memory.get("timestamp")
            if not timestamp_str:
                continue
            
            try:
                # Parse timestamp
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                elif isinstance(timestamp_str, datetime):
                    timestamp = timestamp_str
                else:
                    continue
                
                # Check if within time range
                if start_time <= timestamp <= end_time:
                    filtered.append(memory)
            
            except (ValueError, TypeError):
                continue
        
        return filtered
    
    def is_time_query(self, query: str) -> bool:
        """
        Check if query contains time-related expression.
        
        Args:
            query: Search query
            
        Returns:
            True if time query, False otherwise
        """
        time_keywords = [
            'when', 'last', 'recently', 'lately', 'ago', 'yesterday', 'today',
            'week', 'month', 'year', 'days ago', 'weeks ago', 'months ago'
        ]
        
        query_lower = query.lower()
        return any(kw in query_lower for kw in time_keywords)
