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
Event Importance Scoring

Automatically scores the importance of life events for timeline navigation.
This is a key differentiator from short-term context management systems.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import re


class ImportanceFactor(Enum):
    """Factors that influence event importance"""
    EMOTIONAL_INTENSITY = "emotional_intensity"
    DECISION_IMPACT = "decision_impact"
    TIME_SPAN = "time_span"
    RELATIONSHIPS = "relationships"
    ACHIEVEMENT = "achievement"
    LOSS = "loss"
    FIRST_TIME = "first_time"
    MILESTONE = "milestone"
    LIFE_CHANGE = "life_change"


@dataclass
class EventImportanceScore:
    """
    Detailed importance score for an event.
    
    Attributes:
        total_score: Overall importance score (0.0 - 1.0)
        factors: Dictionary of factor scores
        reason: Human-readable explanation
        is_milestone: Whether this is considered a milestone
        suggested_tags: Suggested tags for the event
    """
    total_score: float = 0.5
    factors: Dict[str, float] = field(default_factory=dict)
    reason: str = ""
    is_milestone: bool = False
    suggested_tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate score range"""
        self.total_score = max(0.0, min(1.0, self.total_score))


class EventImportanceScorer:
    """
    Scores the importance of life events automatically.
    
    This is what makes claw-mem different from short-term context:
    it automatically identifies and highlights major life events.
    
    Scoring factors:
    1. Emotional intensity (words like "amazing", "terrible", "unforgettable")
    2. Decision impact (words like "decided", "chose", "committed")
    3. Time span (duration of the event)
    4. Relationships (people involved)
    5. Achievement (words like "achieved", "completed", "won")
    6. Loss (words like "lost", "died", "ended")
    7. First time (words like "first", "never before")
    8. Milestone (detected by MilestoneDetector)
    9. Life change (words like "moved", "started", "quit")
    """
    
    # Emotional intensity keywords
    EMOTIONAL_KEYWORDS = {
        # Positive emotions (high intensity)
        "amazing": 0.15, "incredible": 0.15, "wonderful": 0.12, "fantastic": 0.12,
        "unforgettable": 0.18, "memorable": 0.10, "best": 0.12, "greatest": 0.15,
        "love": 0.15, "loved": 0.15, "joy": 0.12, "happiness": 0.10,
        "proud": 0.12, "excited": 0.10, "thrilled": 0.12, "grateful": 0.10,
        
        # Negative emotions (high intensity)
        "terrible": 0.15, "horrible": 0.15, "devastating": 0.20, "tragic": 0.18,
        "worst": 0.15, "heartbroken": 0.20, "grief": 0.18, "trauma": 0.20,
        "depressed": 0.15, "anxious": 0.10, "scared": 0.12, "angry": 0.10,
        "disappointed": 0.10, "frustrated": 0.08,
        
        # Medium intensity
        "happy": 0.08, "sad": 0.08, "surprised": 0.06, "confused": 0.04,
        "nervous": 0.06, "calm": 0.02, "relaxed": 0.02,
    }
    
    # Decision impact keywords
    DECISION_KEYWORDS = {
        "decided": 0.15, "decision": 0.12, "chose": 0.12, "choice": 0.10,
        "committed": 0.15, "committed to": 0.18, "resolved": 0.12,
        "determined": 0.10, "made up my mind": 0.15,
    }
    
    # Achievement keywords
    ACHIEVEMENT_KEYWORDS = {
        "achieved": 0.18, "accomplished": 0.18, "completed": 0.12,
        "won": 0.15, "succeeded": 0.15, "success": 0.12,
        "reached": 0.10, "attained": 0.12, "earned": 0.12,
        "graduated": 0.20, "promoted": 0.18, "award": 0.15,
    }
    
    # Loss keywords
    LOSS_KEYWORDS = {
        "lost": 0.18, "died": 0.25, "passed away": 0.25, "death": 0.22,
        "ended": 0.10, "breakup": 0.18, "divorce": 0.20,
        "fired": 0.18, "laid off": 0.18, "bankrupt": 0.20,
        "failed": 0.12, "failure": 0.12,
    }
    
    # First time keywords
    FIRST_TIME_KEYWORDS = {
        "first": 0.15, "first time": 0.20, "never before": 0.15,
        "brand new": 0.10, "debut": 0.12, "initially": 0.05,
    }
    
    # Life change keywords
    LIFE_CHANGE_KEYWORDS = {
        "moved": 0.12, "started": 0.10, "began": 0.08,
        "quit": 0.12, "resigned": 0.12, "left": 0.10,
        "changed": 0.08, "transitioned": 0.10, "shifted": 0.06,
        "married": 0.22, "divorced": 0.20, "engaged": 0.18,
        "pregnant": 0.20, "born": 0.22, "adopted": 0.18,
        "hired": 0.15, "retired": 0.18,
    }
    
    # Time span patterns
    TIME_SPAN_PATTERNS = [
        (r"(\d+)\s*years?", "years", 0.05),      # +0.05 per year
        (r"(\d+)\s*months?", "months", 0.02),    # +0.02 per month
        (r"(\d+)\s*weeks?", "weeks", 0.01),      # +0.01 per week
        (r"(\d+)\s*days?", "days", 0.002),       # +0.002 per day
    ]
    
    # Milestone threshold
    MILESTONE_THRESHOLD = 0.7
    
    def __init__(self):
        """Initialize EventImportanceScorer"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns"""
        self._compiled_time_patterns = [
            (re.compile(pattern, re.IGNORECASE), unit, weight)
            for pattern, unit, weight in self.TIME_SPAN_PATTERNS
        ]
    
    def score(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> EventImportanceScore:
        """
        Score the importance of an event from text.
        
        Args:
            text: The event description text
            metadata: Optional metadata (e.g., people involved, location)
            
        Returns:
            EventImportanceScore with detailed scoring
        """
        text_lower = text.lower()
        factors = {}
        suggested_tags = []
        
        # 1. Emotional intensity
        emotional_score = self._score_emotional_intensity(text_lower)
        if emotional_score > 0:
            factors["emotional_intensity"] = emotional_score
            if emotional_score > 0.15:
                suggested_tags.append("emotional")
        
        # 2. Decision impact
        decision_score = self._score_decision_impact(text_lower)
        if decision_score > 0:
            factors["decision_impact"] = decision_score
            if decision_score > 0.1:
                suggested_tags.append("decision")
        
        # 3. Time span
        time_score = self._score_time_span(text_lower)
        if time_score > 0:
            factors["time_span"] = min(0.2, time_score)  # Cap at 0.2
        
        # 4. Relationships
        relationship_score = self._score_relationships(text_lower, metadata)
        if relationship_score > 0:
            factors["relationships"] = relationship_score
            if relationship_score > 0.1:
                suggested_tags.append("relationship")
        
        # 5. Achievement
        achievement_score = self._score_achievement(text_lower)
        if achievement_score > 0:
            factors["achievement"] = achievement_score
            if achievement_score > 0.1:
                suggested_tags.append("achievement")
        
        # 6. Loss
        loss_score = self._score_loss(text_lower)
        if loss_score > 0:
            factors["loss"] = loss_score
            if loss_score > 0.1:
                suggested_tags.append("loss")
        
        # 7. First time
        first_time_score = self._score_first_time(text_lower)
        if first_time_score > 0:
            factors["first_time"] = first_time_score
            if first_time_score > 0.1:
                suggested_tags.append("first")
        
        # 8. Life change
        life_change_score = self._score_life_change(text_lower)
        if life_change_score > 0:
            factors["life_change"] = life_change_score
            if life_change_score > 0.1:
                suggested_tags.append("life-change")
        
        # Calculate total score
        # Base score is 0.3, add factor scores (capped at 0.7 total addition)
        base_score = 0.3
        factor_sum = sum(factors.values())
        total_score = min(1.0, base_score + min(0.7, factor_sum))
        
        # Determine if milestone
        is_milestone = total_score >= self.MILESTONE_THRESHOLD
        if is_milestone:
            suggested_tags.append("milestone")
        
        # Generate reason
        reason = self._generate_reason(factors, total_score, is_milestone)
        
        return EventImportanceScore(
            total_score=total_score,
            factors=factors,
            reason=reason,
            is_milestone=is_milestone,
            suggested_tags=list(set(suggested_tags)),
        )
    
    def _score_emotional_intensity(self, text: str) -> float:
        """Score emotional intensity from text"""
        score = 0.0
        for keyword, weight in self.EMOTIONAL_KEYWORDS.items():
            if keyword in text:
                score += weight
        return min(0.3, score)  # Cap at 0.3
    
    def _score_decision_impact(self, text: str) -> float:
        """Score decision impact from text"""
        score = 0.0
        for keyword, weight in self.DECISION_KEYWORDS.items():
            if keyword in text:
                score += weight
        return min(0.2, score)
    
    def _score_time_span(self, text: str) -> float:
        """Score time span from text"""
        score = 0.0
        for pattern, unit, weight in self._compiled_time_patterns:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    value = int(match)
                    score += value * weight
                except (ValueError, TypeError):
                    pass
        return min(0.2, score)
    
    def _score_relationships(self, text: str, metadata: Optional[Dict] = None) -> float:
        """Score relationship involvement"""
        score = 0.0
        
        # Keywords indicating relationships
        relationship_keywords = [
            "family", "friend", "partner", "spouse", "husband", "wife",
            "boyfriend", "girlfriend", "child", "parent", "sibling",
            "colleague", "team", "together", "with", "we",
        ]
        
        for keyword in relationship_keywords:
            if keyword in text:
                score += 0.05
        
        # Check metadata for people
        if metadata and "people" in metadata:
            people = metadata.get("people", [])
            score += min(0.1, len(people) * 0.03)
        
        return min(0.15, score)
    
    def _score_achievement(self, text: str) -> float:
        """Score achievement from text"""
        score = 0.0
        for keyword, weight in self.ACHIEVEMENT_KEYWORDS.items():
            if keyword in text:
                score += weight
        return min(0.25, score)
    
    def _score_loss(self, text: str) -> float:
        """Score loss from text"""
        score = 0.0
        for keyword, weight in self.LOSS_KEYWORDS.items():
            if keyword in text:
                score += weight
        return min(0.3, score)
    
    def _score_first_time(self, text: str) -> float:
        """Score first time experience from text"""
        score = 0.0
        for keyword, weight in self.FIRST_TIME_KEYWORDS.items():
            if keyword in text:
                score += weight
        return min(0.2, score)
    
    def _score_life_change(self, text: str) -> float:
        """Score life change from text"""
        score = 0.0
        for keyword, weight in self.LIFE_CHANGE_KEYWORDS.items():
            if keyword in text:
                score += weight
        return min(0.25, score)
    
    def _generate_reason(self, factors: Dict[str, float], total: float, is_milestone: bool) -> str:
        """Generate human-readable reason for the score"""
        if not factors:
            return f"Routine event (score: {total:.2f})"
        
        # Sort factors by score
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)
        top_factors = sorted_factors[:3]
        
        factor_names = {
            "emotional_intensity": "emotional significance",
            "decision_impact": "decision impact",
            "time_span": "time span",
            "relationships": "relationship involvement",
            "achievement": "achievement",
            "loss": "loss",
            "first_time": "first time experience",
            "life_change": "life change",
        }
        
        factor_descriptions = [
            f"{factor_names.get(f, f)} ({s:.2f})"
            for f, s in top_factors
        ]
        
        reason = f"Important due to: {', '.join(factor_descriptions)}"
        if is_milestone:
            reason += " (MILESTONE)"
        
        return reason
    
    def score_event(self, title: str, description: str, metadata: Optional[Dict] = None) -> EventImportanceScore:
        """
        Score an event from title and description.
        
        Args:
            title: Event title
            description: Event description
            metadata: Optional metadata
            
        Returns:
            EventImportanceScore
        """
        combined_text = f"{title} {description}"
        return self.score(combined_text, metadata)
    
    def get_importance_level(self, score: float) -> str:
        """
        Get importance level from score.
        
        Args:
            score: Importance score (0.0 - 1.0)
            
        Returns:
            str: Importance level (critical/high/medium/low)
        """
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def rank_events(self, events: List[Dict]) -> List[Dict]:
        """
        Rank events by importance.
        
        Args:
            events: List of events with 'title' and 'description' keys
            
        Returns:
            List of events sorted by importance (highest first)
        """
        scored_events = []
        
        for event in events:
            title = event.get("title", "")
            description = event.get("description", "")
            metadata = event.get("metadata", {})
            
            score = self.score_event(title, description, metadata)
            scored_events.append({
                "event": event,
                "importance_score": score.total_score,
                "is_milestone": score.is_milestone,
                "suggested_tags": score.suggested_tags,
            })
        
        # Sort by score descending
        scored_events.sort(key=lambda x: x["importance_score"], reverse=True)
        
        return scored_events
