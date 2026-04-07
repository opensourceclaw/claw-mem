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
Milestone Detection

Automatically detects and scores life milestones.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re


class MilestoneType(Enum):
    """Types of life milestones"""
    # Personal milestones
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    GRADUATION = "graduation"
    WEDDING = "wedding"
    BIRTH = "birth"                    # Having a child
    DEATH = "death"                    # Loss of loved one
    
    # Career milestones
    NEW_JOB = "new_job"
    PROMOTION = "promotion"
    RETIREMENT = "retirement"
    BUSINESS_START = "business_start"
    BUSINESS_EXIT = "business_exit"
    
    # Education milestones
    DEGREE = "degree"
    CERTIFICATION = "certification"
    COURSE = "course"
    
    # Travel milestones
    TRIP = "trip"
    MOVE = "move"                      # Moving to new home/city
    
    # Achievement milestones
    AWARD = "award"
    PUBLICATION = "publication"
    PROJECT = "project"
    
    # Relationship milestones
    RELATIONSHIP_START = "relationship_start"
    RELATIONSHIP_END = "relationship_end"
    FRIENDSHIP = "friendship"
    
    # Personal growth
    SKILL = "skill"
    HOBBY = "hobby"
    CHALLENGE = "challenge"
    
    # Other
    OTHER = "other"


@dataclass
class MilestonePattern:
    """Pattern for detecting milestones"""
    milestone_type: MilestoneType
    keywords: List[str]
    patterns: List[str]  # Regex patterns
    importance_boost: float  # Boost to importance score


class MilestoneDetector:
    """
    Detects life milestones from memory content.
    
    This is what makes claw-mem different from short-term context:
    it recognizes and highlights major life events.
    """
    
    # Patterns for milestone detection
    MILESTONE_PATTERNS: List[MilestonePattern] = [
        # Personal milestones
        MilestonePattern(
            milestone_type=MilestoneType.BIRTHDAY,
            keywords=["birthday", "birthday party", "turned"],
            patterns=[r"turned \d+", r"\d+th birthday", r"birthday party"],
            importance_boost=0.3,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.WEDDING,
            keywords=["wedding", "married", "marriage", "got married"],
            patterns=[r"got married", r"wedding ceremony", r"we married"],
            importance_boost=0.5,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.GRADUATION,
            keywords=["graduation", "graduated", "degree"],
            patterns=[r"graduated from", r"graduation ceremony", r"earned.*degree"],
            importance_boost=0.4,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.BIRTH,
            keywords=["born", "baby", "child", "son", "daughter", "pregnancy"],
            patterns=[r"baby.*born", r"gave birth", r"my (son|daughter)"],
            importance_boost=0.5,
        ),
        
        # Career milestones
        MilestonePattern(
            milestone_type=MilestoneType.NEW_JOB,
            keywords=["new job", "hired", "started working", "joined"],
            patterns=[r"started.*job", r"new job.*at", r"hired by", r"joined.*team"],
            importance_boost=0.4,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.PROMOTION,
            keywords=["promotion", "promoted", "senior", "lead", "manager"],
            patterns=[r"promoted to", r"became.*manager", r"senior.*position"],
            importance_boost=0.35,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.BUSINESS_START,
            keywords=["started business", "startup", "company", "entrepreneur"],
            patterns=[r"started.*business", r"founded.*company", r"launched.*startup"],
            importance_boost=0.45,
        ),
        
        # Education milestones
        MilestonePattern(
            milestone_type=MilestoneType.DEGREE,
            keywords=["degree", "bachelor", "master", "phd", "doctorate"],
            patterns=[r"earned.*degree", r"bachelor.*degree", r"master.*degree", r"phd"],
            importance_boost=0.4,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.CERTIFICATION,
            keywords=["certification", "certified", "certificate"],
            patterns=[r"certified in", r"got.*certification", r"passed.*exam"],
            importance_boost=0.25,
        ),
        
        # Travel milestones
        MilestonePattern(
            milestone_type=MilestoneType.TRIP,
            keywords=["trip", "travel", "vacation", "visited", "journey"],
            patterns=[r"traveled to", r"trip to", r"visited", r"vacation in"],
            importance_boost=0.2,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.MOVE,
            keywords=["moved", "relocated", "new home", "new city", "new apartment"],
            patterns=[r"moved to", r"relocated to", r"new home in"],
            importance_boost=0.35,
        ),
        
        # Achievement milestones
        MilestonePattern(
            milestone_type=MilestoneType.AWARD,
            keywords=["award", "prize", "winner", "won", "achievement"],
            patterns=[r"won.*award", r"received.*prize", r"achievement award"],
            importance_boost=0.35,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.PUBLICATION,
            keywords=["published", "paper", "article", "book"],
            patterns=[r"published.*paper", r"published.*article", r"wrote.*book"],
            importance_boost=0.3,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.PROJECT,
            keywords=["project", "launched", "released", "completed"],
            patterns=[r"launched.*project", r"released.*product", r"completed.*project"],
            importance_boost=0.25,
        ),
        
        # Relationship milestones
        MilestonePattern(
            milestone_type=MilestoneType.RELATIONSHIP_START,
            keywords=["dating", "relationship", "boyfriend", "girlfriend", "partner"],
            patterns=[r"started dating", r"in a relationship", r"my partner"],
            importance_boost=0.3,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.RELATIONSHIP_END,
            keywords=["breakup", "divorce", "separated", "ended"],
            patterns=[r"broke up", r"divorce", r"ended.*relationship"],
            importance_boost=0.35,
        ),
        
        # Personal growth
        MilestonePattern(
            milestone_type=MilestoneType.SKILL,
            keywords=["learned", "skill", "mastered", "trained"],
            patterns=[r"learned to", r"mastered", r"trained in"],
            importance_boost=0.2,
        ),
        MilestonePattern(
            milestone_type=MilestoneType.CHALLENGE,
            keywords=["challenge", "overcome", "struggle", "difficulty"],
            patterns=[r"overcame.*challenge", r"faced.*difficulty", r"struggled with"],
            importance_boost=0.25,
        ),
    ]
    
    def __init__(self):
        """Initialize MilestoneDetector"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self._compiled_patterns: List[Tuple[MilestoneType, re.Pattern, float]] = []
        for mp in self.MILESTONE_PATTERNS:
            for pattern in mp.patterns:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self._compiled_patterns.append((mp.milestone_type, compiled, mp.importance_boost))
                except re.error:
                    pass  # Skip invalid patterns
    
    def detect(self, text: str, base_importance: float = 0.5) -> List[Tuple[MilestoneType, float]]:
        """
        Detect milestones in text.
        
        Args:
            text: The text to analyze
            base_importance: Base importance score
            
        Returns:
            List of (MilestoneType, importance_score) tuples
        """
        detected = []
        text_lower = text.lower()
        
        for mp in self.MILESTONE_PATTERNS:
            # Check keywords
            keyword_match = any(kw in text_lower for kw in mp.keywords)
            
            # Check patterns
            pattern_match = False
            for pattern in mp.patterns:
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        pattern_match = True
                        break
                except re.error:
                    pass
            
            if keyword_match or pattern_match:
                importance = min(1.0, base_importance + mp.importance_boost)
                detected.append((mp.milestone_type, importance))
        
        return detected
    
    def score_milestone(self, text: str, base_importance: float = 0.5) -> float:
        """
        Score the milestone importance of text.
        
        Args:
            text: The text to analyze
            base_importance: Base importance score
            
        Returns:
            Importance score (0.0 - 1.0)
        """
        detected = self.detect(text, base_importance)
        if not detected:
            return base_importance
        
        # Return highest importance
        return max(score for _, score in detected)
    
    def get_milestone_type(self, text: str) -> Optional[MilestoneType]:
        """
        Get the primary milestone type from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Primary MilestoneType or None
        """
        detected = self.detect(text)
        if not detected:
            return None
        
        # Return highest scoring type
        return max(detected, key=lambda x: x[1])[0]
    
    def is_milestone(self, text: str, threshold: float = 0.6) -> bool:
        """
        Check if text describes a milestone.
        
        Args:
            text: The text to analyze
            threshold: Importance threshold
            
        Returns:
            True if milestone score >= threshold
        """
        return self.score_milestone(text) >= threshold
