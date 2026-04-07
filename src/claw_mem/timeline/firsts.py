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
First Events Detection

Detect and track "first time" experiences in life.

These are memorable first experiences that shape who we are.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class FirstEventType(Enum):
    """Types of first-time events"""
    # Personal firsts
    FIRST_WORD = "first_word"              # First word spoken
    FIRST_STEP = "first_step"              # First step walked
    FIRST_DAY_SCHOOL = "first_day_school"  # First day of school
    FIRST_FRIEND = "first_friend"          # First friend
    FIRST_LOVE = "first_love"              # First love
    FIRST_HEARTBREAK = "first_heartbreak"  # First heartbreak
    
    # Career firsts
    FIRST_JOB = "first_job"                # First job
    FIRST_PAYCHECK = "first_paycheck"      # First paycheck
    FIRST_PROMOTION = "first_promotion"    # First promotion
    FIRST_BUSINESS = "first_business"      # First business
    
    # Education firsts
    FIRST_DEGREE = "first_degree"          # First degree
    FIRST_PUBLICATION = "first_publication" # First publication
    FIRST_AWARD = "first_award"            # First award
    
    # Experience firsts
    FIRST_TRIP = "first_trip"              # First trip
    FIRST_FLIGHT = "first_flight"          # First flight
    FIRST_CAR = "first_car"                # First car
    FIRST_HOME = "first_home"              # First home
    
    # Skill firsts
    FIRST_CODE = "first_code"              # First code written
    FIRST_ART = "first_art"                # First artwork
    FIRST_SONG = "first_song"              # First song
    FIRST_SPORT = "first_sport"            # First sport
    
    # Digital firsts
    FIRST_COMPUTER = "first_computer"      # First computer
    FIRST_PHONE = "first_phone"            # First phone
    FIRST_EMAIL = "first_email"            # First email
    FIRST_SOCIAL = "first_social"          # First social media
    
    # Other
    OTHER = "other"


@dataclass
class FirstEvent:
    """
    A "first time" experience.
    
    These are memorable first experiences that shape who we are.
    
    Attributes:
        event_id: Unique identifier
        event_type: Type of first event
        title: Event title
        description: Detailed description
        timestamp: When it happened
        location: Where it happened
        people: People involved
        emotions: Emotions felt
        importance: Importance score
        impact: Life impact description
        memories: Related memory IDs
        metadata: Additional metadata
    """
    event_id: str
    event_type: FirstEventType
    title: str
    description: str
    timestamp: datetime
    location: Optional[str] = None
    people: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    importance: float = 0.7  # First events are inherently important
    impact: Optional[str] = None
    memories: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location,
            "people": self.people,
            "emotions": self.emotions,
            "importance": self.importance,
            "impact": self.impact,
            "memories": self.memories,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "FirstEvent":
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=FirstEventType(data["event_type"]),
            title=data["title"],
            description=data["description"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            location=data.get("location"),
            people=data.get("people", []),
            emotions=data.get("emotions", []),
            importance=data.get("importance", 0.7),
            impact=data.get("impact"),
            memories=data.get("memories", []),
            metadata=data.get("metadata", {}),
        )


class FirstEventsDetector:
    """
    Detects "first time" experiences from memory content.
    
    These are what make claw-mem truly different from short-term
    context management - we remember the firsts that shaped us.
    """
    
    # Patterns for detecting first events
    FIRST_PATTERNS = [
        # Personal firsts
        (FirstEventType.FIRST_WORD, [r"first word", r"first spoke", r"said.*first"]),
        (FirstEventType.FIRST_STEP, [r"first step", r"first walked", r"started walking"]),
        (FirstEventType.FIRST_DAY_SCHOOL, [r"first day.*school", r"started school", r"first day at school"]),
        (FirstEventType.FIRST_FRIEND, [r"first friend", r"made.*first friend", r"met.*first friend"]),
        (FirstEventType.FIRST_LOVE, [r"first love", r"fell in love.*first", r"first relationship"]),
        (FirstEventType.FIRST_HEARTBREAK, [r"first heartbreak", r"heartbroken.*first", r"first breakup"]),
        
        # Career firsts
        (FirstEventType.FIRST_JOB, [r"first job", r"started working.*first", r"first day.*work"]),
        (FirstEventType.FIRST_PAYCHECK, [r"first paycheck", r"first salary", r"got paid.*first"]),
        (FirstEventType.FIRST_PROMOTION, [r"first promotion", r"promoted.*first time"]),
        (FirstEventType.FIRST_BUSINESS, [r"first business", r"started.*first company"]),
        
        # Education firsts
        (FirstEventType.FIRST_DEGREE, [r"first degree", r"graduated.*first", r"bachelor.*first"]),
        (FirstEventType.FIRST_PUBLICATION, [r"first publication", r"published.*first", r"first paper"]),
        (FirstEventType.FIRST_AWARD, [r"first award", r"won.*first prize", r"first prize"]),
        
        # Experience firsts
        (FirstEventType.FIRST_TRIP, [r"first trip", r"traveled.*first time", r"first time traveling"]),
        (FirstEventType.FIRST_FLIGHT, [r"first flight", r"flew.*first time", r"first time.*plane"]),
        (FirstEventType.FIRST_CAR, [r"first car", r"bought.*first car", r"got.*first car"]),
        (FirstEventType.FIRST_HOME, [r"first home", r"first house", r"first apartment"]),
        
        # Skill firsts
        (FirstEventType.FIRST_CODE, [r"first code", r"first program", r"coded.*first", r"programmed.*first"]),
        (FirstEventType.FIRST_ART, [r"first painting", r"first drawing", r"first artwork"]),
        (FirstEventType.FIRST_SONG, [r"first song", r"first music", r"first concert"]),
        (FirstEventType.FIRST_SPORT, [r"first game", r"first match", r"first tournament"]),
        
        # Digital firsts
        (FirstEventType.FIRST_COMPUTER, [r"first computer", r"got.*first computer"]),
        (FirstEventType.FIRST_PHONE, [r"first phone", r"first smartphone", r"got.*first phone"]),
        (FirstEventType.FIRST_EMAIL, [r"first email", r"first email account"]),
        (FirstEventType.FIRST_SOCIAL, [r"first social media", r"first facebook", r"first twitter"]),
    ]
    
    # Additional "first" keywords
    FIRST_KEYWORDS = [
        "first time", "my first", "the first", "for the first time",
        "first ever", "never before", "brand new experience",
    ]
    
    def __init__(self):
        """Initialize FirstEventsDetector"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns"""
        self._compiled: List[Tuple[FirstEventType, re.Pattern]] = []
        for event_type, patterns in self.FIRST_PATTERNS:
            for pattern in patterns:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self._compiled.append((event_type, compiled))
                except re.error:
                    pass
    
    def detect(self, text: str) -> List[Tuple[FirstEventType, str, float]]:
        """
        Detect first events in text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of (FirstEventType, matched_text, confidence) tuples
        """
        detected = []
        text_lower = text.lower()
        
        # Check for generic "first" keywords
        has_first_keyword = any(kw in text_lower for kw in self.FIRST_KEYWORDS)
        
        # Check specific patterns
        for event_type, pattern in self._compiled:
            match = pattern.search(text)
            if match:
                confidence = 0.9 if has_first_keyword else 0.7
                detected.append((event_type, match.group(), confidence))
        
        return detected
    
    def get_first_event_type(self, text: str) -> Optional[FirstEventType]:
        """
        Get the primary first event type from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            FirstEventType or None
        """
        detected = self.detect(text)
        if not detected:
            return None
        
        # Return highest confidence type
        return max(detected, key=lambda x: x[2])[0]
    
    def is_first_event(self, text: str) -> bool:
        """
        Check if text describes a first event.
        
        Args:
            text: The text to analyze
            
        Returns:
            True if first event detected
        """
        text_lower = text.lower()
        
        # Check keywords
        if any(kw in text_lower for kw in self.FIRST_KEYWORDS):
            return True
        
        # Check patterns
        for _, pattern in self._compiled:
            if pattern.search(text):
                return True
        
        return False
    
    def extract_first_event(self, text: str, timestamp: Optional[datetime] = None) -> Optional[FirstEvent]:
        """
        Extract a first event from text.
        
        Args:
            text: The text to analyze
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            FirstEvent or None
        """
        detected = self.detect(text)
        if not detected:
            return None
        
        # Get highest confidence detection
        event_type, matched, confidence = max(detected, key=lambda x: x[2])
        
        import uuid
        return FirstEvent(
            event_id=f"first_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            title=f"First {event_type.value.replace('_', ' ')}",
            description=text,
            timestamp=timestamp or datetime.now(),
            importance=0.7 + (confidence * 0.2),  # 0.7 - 0.9
        )
    
    def score_first_event(self, text: str) -> float:
        """
        Score the likelihood of text describing a first event.
        
        Args:
            text: The text to analyze
            
        Returns:
            Score (0.0 - 1.0)
        """
        detected = self.detect(text)
        if not detected:
            return 0.0
        
        # Return highest confidence
        return max(conf for _, _, conf in detected)
    
    def get_first_event_suggestions(self, text: str) -> List[str]:
        """
        Get suggestions for what "first" this might be.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of suggestions
        """
        detected = self.detect(text)
        suggestions = []
        
        for event_type, matched, confidence in detected:
            suggestion = f"This might be your first {event_type.value.replace('_', ' ')}"
            if confidence > 0.8:
                suggestion += " (high confidence)"
            elif confidence > 0.6:
                suggestion += " (medium confidence)"
            suggestions.append(suggestion)
        
        return suggestions
