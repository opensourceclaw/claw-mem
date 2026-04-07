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
Decision Tracking

Track important decisions in life.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
from pathlib import Path
import json
import uuid


class DecisionStatus(Enum):
    """Status of a decision"""
    MADE = "made"                # Decision made, executing
    COMPLETED = "completed"      # Decision executed, outcome known
    REVISED = "revised"          # Decision revised
    ABANDONED = "abandoned"      # Decision abandoned


class DecisionType(Enum):
    """Type of decision"""
    CAREER = "career"            # Career decisions
    EDUCATION = "education"      # Education decisions
    FINANCIAL = "financial"      # Financial decisions
    RELATIONSHIP = "relationship" # Relationship decisions
    HEALTH = "health"            # Health decisions
    LIFESTYLE = "lifestyle"      # Lifestyle decisions
    LOCATION = "location"        # Location/moving decisions
    PROJECT = "project"          # Project decisions
    OTHER = "other"              # Other decisions


@dataclass
class Decision:
    """
    A life decision.
    
    Decisions are key moments in life that shape the future.
    Tracking them helps understand life trajectory.
    
    Attributes:
        decision_id: Unique identifier
        title: Decision title
        description: Detailed description
        decision_type: Type of decision
        status: Current status
        made_at: When decision was made
        options: Available options at the time
        chosen_option: The option chosen
        reasoning: Reasoning behind the decision
        expected_outcome: What was expected
        actual_outcome: What actually happened (if known)
        importance: Importance score (0.0 - 1.0)
        tags: List of tags
        related_events: IDs of related timeline events
        lessons_learned: Lessons learned from this decision
        metadata: Additional metadata
    """
    decision_id: str
    title: str
    description: str
    decision_type: DecisionType
    status: DecisionStatus
    made_at: datetime
    options: List[str] = field(default_factory=list)
    chosen_option: Optional[str] = None
    reasoning: Optional[str] = None
    expected_outcome: Optional[str] = None
    actual_outcome: Optional[str] = None
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "description": self.description,
            "decision_type": self.decision_type.value,
            "status": self.status.value,
            "made_at": self.made_at.isoformat(),
            "options": self.options,
            "chosen_option": self.chosen_option,
            "reasoning": self.reasoning,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "importance": self.importance,
            "tags": self.tags,
            "related_events": self.related_events,
            "lessons_learned": self.lessons_learned,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """Create from dictionary"""
        return cls(
            decision_id=data["decision_id"],
            title=data["title"],
            description=data["description"],
            decision_type=DecisionType(data["decision_type"]),
            status=DecisionStatus(data["status"]),
            made_at=datetime.fromisoformat(data["made_at"]),
            options=data.get("options", []),
            chosen_option=data.get("chosen_option"),
            reasoning=data.get("reasoning"),
            expected_outcome=data.get("expected_outcome"),
            actual_outcome=data.get("actual_outcome"),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            related_events=data.get("related_events", []),
            lessons_learned=data.get("lessons_learned", []),
            metadata=data.get("metadata", {}),
        )


class DecisionTracker:
    """
    Track important life decisions.
    
    This helps users understand their decision-making patterns
    and learn from past decisions.
    """
    
    # Keywords for detecting decisions
    DECISION_KEYWORDS = [
        "decided", "decision", "chose", "choice", "selected",
        "made up my mind", "going to", "will", "planning to",
        "committed to", "signed up for", "enrolled in",
        "accepted", "rejected", "declined", "quit", "resigned",
    ]
    
    # Decision type patterns
    TYPE_PATTERNS = {
        DecisionType.CAREER: ["job", "career", "work", "company", "position", "promotion"],
        DecisionType.EDUCATION: ["school", "university", "college", "course", "degree", "study"],
        DecisionType.FINANCIAL: ["invest", "buy", "sell", "money", "budget", "loan"],
        DecisionType.RELATIONSHIP: ["marriage", "dating", "partner", "relationship", "family"],
        DecisionType.HEALTH: ["health", "exercise", "diet", "doctor", "treatment"],
        DecisionType.LIFESTYLE: ["lifestyle", "hobby", "habit", "routine"],
        DecisionType.LOCATION: ["move", "city", "house", "apartment", "location"],
        DecisionType.PROJECT: ["project", "build", "create", "start"],
    }
    
    def __init__(self, workspace: Path):
        """
        Initialize DecisionTracker.
        
        Args:
            workspace: Path to claw-mem workspace
        """
        self.workspace = workspace
        self.decisions_dir = workspace / "decisions"
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self._decisions: Dict[str, Decision] = {}
        self._load_decisions()
    
    def _load_decisions(self):
        """Load decisions from disk"""
        decisions_file = self.decisions_dir / "decisions.json"
        if decisions_file.exists():
            with open(decisions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for decision_data in data.get("decisions", []):
                    decision = Decision.from_dict(decision_data)
                    self._decisions[decision.decision_id] = decision
    
    def _save_decisions(self):
        """Save decisions to disk"""
        decisions_file = self.decisions_dir / "decisions.json"
        data = {
            "decisions": [d.to_dict() for d in self._decisions.values()],
            "updated_at": datetime.now().isoformat(),
        }
        with open(decisions_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_decision(
        self,
        title: str,
        description: str,
        decision_type: DecisionType,
        options: Optional[List[str]] = None,
        chosen_option: Optional[str] = None,
        reasoning: Optional[str] = None,
        importance: float = 0.5,
    ) -> Decision:
        """
        Add a new decision.
        
        Args:
            title: Decision title
            description: Detailed description
            decision_type: Type of decision
            options: Available options
            chosen_option: The option chosen
            reasoning: Reasoning behind the decision
            importance: Importance score
            
        Returns:
            The created Decision
        """
        decision = Decision(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            decision_type=decision_type,
            status=DecisionStatus.MADE,
            made_at=datetime.now(),
            options=options or [],
            chosen_option=chosen_option,
            reasoning=reasoning,
            importance=importance,
        )
        
        self._decisions[decision.decision_id] = decision
        self._save_decisions()
        
        return decision
    
    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """
        Get a decision by ID.
        
        Args:
            decision_id: The decision ID
            
        Returns:
            Decision or None
        """
        return self._decisions.get(decision_id)
    
    def update_decision(
        self,
        decision_id: str,
        status: Optional[DecisionStatus] = None,
        actual_outcome: Optional[str] = None,
        lessons_learned: Optional[List[str]] = None,
    ) -> Optional[Decision]:
        """
        Update a decision.
        
        Args:
            decision_id: The decision ID
            status: New status
            actual_outcome: Actual outcome
            lessons_learned: Lessons learned
            
        Returns:
            Updated Decision or None
        """
        decision = self._decisions.get(decision_id)
        if not decision:
            return None
        
        if status:
            decision.status = status
        if actual_outcome:
            decision.actual_outcome = actual_outcome
        if lessons_learned:
            decision.lessons_learned.extend(lessons_learned)
        
        self._save_decisions()
        return decision
    
    def get_decisions(
        self,
        decision_type: Optional[DecisionType] = None,
        status: Optional[DecisionStatus] = None,
        limit: int = 100,
    ) -> List[Decision]:
        """
        Get decisions with optional filters.
        
        Args:
            decision_type: Filter by type
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of Decision
        """
        results = []
        
        for decision in self._decisions.values():
            if decision_type and decision.decision_type != decision_type:
                continue
            if status and decision.status != status:
                continue
            results.append(decision)
        
        # Sort by date (most recent first)
        results.sort(key=lambda d: d.made_at, reverse=True)
        
        return results[:limit]
    
    def detect_decision(self, text: str) -> bool:
        """
        Detect if text contains a decision.
        
        Args:
            text: The text to analyze
            
        Returns:
            True if decision detected
        """
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.DECISION_KEYWORDS)
    
    def classify_decision_type(self, text: str) -> DecisionType:
        """
        Classify the type of decision from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            DecisionType
        """
        text_lower = text.lower()
        
        for decision_type, keywords in self.TYPE_PATTERNS.items():
            if any(kw in text_lower for kw in keywords):
                return decision_type
        
        return DecisionType.OTHER
    
    def get_decision_context(self, query: str) -> Dict[str, Any]:
        """
        Get decision context for a query.
        
        Args:
            query: The query string
            
        Returns:
            Dictionary with decision context
        """
        # Detect decision type
        decision_type = self.classify_decision_type(query)
        
        # Get related decisions
        related = self.get_decisions(decision_type=decision_type, limit=5)
        
        return {
            "query": query,
            "detected_type": decision_type.value,
            "related_decisions": [d.to_dict() for d in related],
            "total_decisions": len(self._decisions),
        }
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """
        Get decision statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self._decisions)
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for decision in self._decisions.values():
            type_name = decision.decision_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Count by status
        status_counts: Dict[str, int] = {}
        for decision in self._decisions.values():
            status_name = decision.status.value
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        return {
            "total_decisions": total,
            "by_type": type_counts,
            "by_status": status_counts,
        }
