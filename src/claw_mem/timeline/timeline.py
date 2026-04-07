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
Timeline API

Provides life timeline navigation for claw-mem.

This module enables users to navigate their digital life through time,
making claw-mem different from short-term context management systems.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum
from pathlib import Path
import json


class EventType(Enum):
    """Types of life events"""
    MILESTONE = "milestone"          # Major life events
    DECISION = "decision"            # Important decisions
    FIRST_TIME = "first_time"        # First time experiences
    ROUTINE = "routine"              # Regular activities
    EMOTIONAL = "emotional"          # Emotionally significant events
    LEARNING = "learning"            # Learning experiences
    RELATIONSHIP = "relationship"    # Relationship events
    CAREER = "career"                # Career events
    TRAVEL = "travel"                # Travel experiences
    ACHIEVEMENT = "achievement"      # Personal achievements
    OTHER = "other"                  # Other events


@dataclass
class TimelineEvent:
    """
    A life event in the timeline.
    
    Attributes:
        event_id: Unique identifier
        title: Event title
        description: Detailed description
        event_type: Type of event
        timestamp: When it happened
        end_timestamp: Optional end time (for duration events)
        importance: Importance score (0.0 - 1.0)
        emotions: List of emotions associated
        tags: List of tags
        people: People involved
        location: Where it happened
        metadata: Additional metadata
        source_memory_ids: IDs of source memories
    """
    event_id: str
    title: str
    description: str
    event_type: EventType
    timestamp: datetime
    end_timestamp: Optional[datetime] = None
    importance: float = 0.5
    emotions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_memory_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "end_timestamp": self.end_timestamp.isoformat() if self.end_timestamp else None,
            "importance": self.importance,
            "emotions": self.emotions,
            "tags": self.tags,
            "people": self.people,
            "location": self.location,
            "metadata": self.metadata,
            "source_memory_ids": self.source_memory_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineEvent":
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            title=data["title"],
            description=data["description"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            end_timestamp=datetime.fromisoformat(data["end_timestamp"]) if data.get("end_timestamp") else None,
            importance=data.get("importance", 0.5),
            emotions=data.get("emotions", []),
            tags=data.get("tags", []),
            people=data.get("people", []),
            location=data.get("location"),
            metadata=data.get("metadata", {}),
            source_memory_ids=data.get("source_memory_ids", []),
        )
    
    @property
    def year(self) -> int:
        """Get year of event"""
        return self.timestamp.year
    
    @property
    def month(self) -> int:
        """Get month of event"""
        return self.timestamp.month
    
    @property
    def day(self) -> int:
        """Get day of event"""
        return self.timestamp.day
    
    @property
    def weekday(self) -> int:
        """Get weekday (0 = Monday, 6 = Sunday)"""
        return self.timestamp.weekday()
    
    @property
    def duration_days(self) -> Optional[int]:
        """Get duration in days if end_timestamp is set"""
        if self.end_timestamp:
            return (self.end_timestamp - self.timestamp).days
        return None


@dataclass
class TimelineQuery:
    """
    Query for timeline events.
    
    Attributes:
        start_date: Start of date range
        end_date: End of date range
        event_types: Filter by event types
        min_importance: Minimum importance score
        emotions: Filter by emotions
        tags: Filter by tags
        people: Filter by people involved
        location: Filter by location
        text_search: Search in title/description
        limit: Maximum number of results
    """
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    event_types: Optional[List[EventType]] = None
    min_importance: float = 0.0
    emotions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    people: Optional[List[str]] = None
    location: Optional[str] = None
    text_search: Optional[str] = None
    limit: int = 100


class Timeline:
    """
    Timeline API for navigating life events.
    
    This is the core API for "your digital life, preserved forever".
    Different from short-term context management (like OpenClaw Dream),
    Timeline focuses on long-term life events and milestones.
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize Timeline.
        
        Args:
            workspace: Path to claw-mem workspace
        """
        self.workspace = workspace
        self.timeline_dir = workspace / "timeline"
        self.timeline_dir.mkdir(parents=True, exist_ok=True)
        self.events_index: Dict[str, str] = {}  # event_id -> file_path
        self._load_index()
    
    def _load_index(self):
        """Load events index"""
        index_file = self.timeline_dir / "index.json"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                self.events_index = json.load(f)
    
    def _save_index(self):
        """Save events index"""
        index_file = self.timeline_dir / "index.json"
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(self.events_index, f, indent=2, ensure_ascii=False)
    
    def _get_year_file(self, year: int) -> Path:
        """Get file path for a year"""
        return self.timeline_dir / f"year_{year}.json"
    
    def add_event(self, event: TimelineEvent) -> str:
        """
        Add a life event to the timeline.
        
        Args:
            event: The event to add
            
        Returns:
            Event ID
        """
        year = event.year
        year_file = self._get_year_file(year)
        
        # Load existing events for the year
        events = []
        if year_file.exists():
            with open(year_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        
        # Add new event
        events.append(event.to_dict())
        
        # Sort by timestamp
        events.sort(key=lambda e: e["timestamp"])
        
        # Save
        with open(year_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        # Update index
        self.events_index[event.event_id] = str(year_file)
        self._save_index()
        
        return event.event_id
    
    def get_event(self, event_id: str) -> Optional[TimelineEvent]:
        """
        Get a specific event by ID.
        
        Args:
            event_id: The event ID
            
        Returns:
            TimelineEvent or None if not found
        """
        if event_id not in self.events_index:
            return None
        
        file_path = Path(self.events_index[event_id])
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            events = json.load(f)
        
        for event_data in events:
            if event_data["event_id"] == event_id:
                return TimelineEvent.from_dict(event_data)
        
        return None
    
    def get_life_events(self, year: int) -> List[TimelineEvent]:
        """
        Get all life events for a specific year.
        
        Args:
            year: The year to query
            
        Returns:
            List of TimelineEvent
        """
        year_file = self._get_year_file(year)
        if not year_file.exists():
            return []
        
        with open(year_file, "r", encoding="utf-8") as f:
            events_data = json.load(f)
        
        return [TimelineEvent.from_dict(e) for e in events_data]
    
    def get_milestones(self, year: Optional[int] = None) -> List[TimelineEvent]:
        """
        Get milestone events.
        
        Milestones are major life events with high importance.
        
        Args:
            year: Optional year filter
            
        Returns:
            List of milestone TimelineEvent
        """
        query = TimelineQuery(
            event_types=[EventType.MILESTONE],
            min_importance=0.7,
        )
        if year:
            query.start_date = date(year, 1, 1)
            query.end_date = date(year, 12, 31)
        
        return self.query(query)
    
    def get_decisions(self, year: Optional[int] = None) -> List[TimelineEvent]:
        """
        Get important decisions.
        
        Args:
            year: Optional year filter
            
        Returns:
            List of decision TimelineEvent
        """
        query = TimelineQuery(
            event_types=[EventType.DECISION],
            min_importance=0.6,
        )
        if year:
            query.start_date = date(year, 1, 1)
            query.end_date = date(year, 12, 31)
        
        return self.query(query)
    
    def get_firsts(self) -> List[TimelineEvent]:
        """
        Get "first time" events.
        
        These are memorable first experiences in life.
        
        Returns:
            List of first-time TimelineEvent
        """
        query = TimelineQuery(
            event_types=[EventType.FIRST_TIME],
            min_importance=0.5,
        )
        return self.query(query)
    
    def search_by_emotion(self, emotion: str) -> List[TimelineEvent]:
        """
        Search events by emotion.
        
        Args:
            emotion: The emotion to search for (e.g., "happy", "sad", "excited")
            
        Returns:
            List of matching TimelineEvent
        """
        query = TimelineQuery(
            emotions=[emotion.lower()],
        )
        return self.query(query)
    
    def query(self, query: TimelineQuery) -> List[TimelineEvent]:
        """
        Query timeline events with filters.
        
        Args:
            query: TimelineQuery with filter criteria
            
        Returns:
            List of matching TimelineEvent
        """
        results = []
        
        # Determine which year files to search
        if query.start_date and query.end_date:
            years = range(query.start_date.year, query.end_date.year + 1)
        else:
            # Search all years
            years = sorted(set(
                int(f.stem.split("_")[1])
                for f in self.timeline_dir.glob("year_*.json")
            ))
        
        for year in years:
            year_file = self._get_year_file(year)
            if not year_file.exists():
                continue
            
            with open(year_file, "r", encoding="utf-8") as f:
                events_data = json.load(f)
            
            for event_data in events_data:
                event = TimelineEvent.from_dict(event_data)
                
                # Apply filters
                if not self._matches_query(event, query):
                    continue
                
                results.append(event)
                
                if len(results) >= query.limit:
                    return results
        
        return results
    
    def _matches_query(self, event: TimelineEvent, query: TimelineQuery) -> bool:
        """Check if event matches query criteria"""
        # Date range filter
        if query.start_date and event.timestamp.date() < query.start_date:
            return False
        if query.end_date and event.timestamp.date() > query.end_date:
            return False
        
        # Event type filter
        if query.event_types and event.event_type not in query.event_types:
            return False
        
        # Importance filter
        if event.importance < query.min_importance:
            return False
        
        # Emotions filter
        if query.emotions:
            if not any(e in [em.lower() for em in event.emotions] for e in query.emotions):
                return False
        
        # Tags filter
        if query.tags:
            if not any(t in event.tags for t in query.tags):
                return False
        
        # People filter
        if query.people:
            if not any(p in event.people for p in query.people):
                return False
        
        # Location filter
        if query.location and event.location:
            if query.location.lower() not in event.location.lower():
                return False
        
        # Text search
        if query.text_search:
            search_lower = query.text_search.lower()
            if (search_lower not in event.title.lower() and
                search_lower not in event.description.lower()):
                return False
        
        return True
    
    def get_timeline_context(self, query: str, max_events: int = 10) -> Dict[str, Any]:
        """
        Get timeline context for a query.
        
        This is the main API for integrating with AI assistants.
        Returns relevant life events that provide context.
        
        Args:
            query: The query string
            max_events: Maximum number of events to return
            
        Returns:
            Dictionary with timeline context
        """
        # Search by text
        text_results = self.query(TimelineQuery(
            text_search=query,
            limit=max_events,
        ))
        
        # Get recent milestones
        milestones = self.query(TimelineQuery(
            event_types=[EventType.MILESTONE],
            min_importance=0.7,
            limit=5,
        ))
        
        return {
            "query": query,
            "matching_events": [e.to_dict() for e in text_results],
            "recent_milestones": [e.to_dict() for e in milestones],
            "total_events": len(self.events_index),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get timeline statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_events = len(self.events_index)
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for event_id, file_path in self.events_index.items():
            event = self.get_event(event_id)
            if event:
                type_name = event.event_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Get year range
        years = sorted(set(
            int(f.stem.split("_")[1])
            for f in self.timeline_dir.glob("year_*.json")
        ))
        
        return {
            "total_events": total_events,
            "event_types": type_counts,
            "year_range": [years[0], years[-1]] if years else None,
            "total_years": len(years),
        }
