"""
claw-mem v2.10.0 - Experience Classifier

Evaluates whether an experience is worth consolidating into weights.
Four dimensions:
  - Frequency: how often the pattern repeats
  - Importance: task contribution value
  - Novelty: knowledge difference from existing weights
  - Durability: cross-session persistence value
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re
import math


@dataclass
class ExperienceScore:
    """Scoring breakdown for an experience."""
    frequency: float = 0.0    # 0-1: how often seen
    importance: float = 0.0   # 0-1: task relevance
    novelty: float = 0.0      # 0-1: how new/different
    durability: float = 0.0   # 0-1: long-term value

    @property
    def total(self) -> float:
        """Weighted total score."""
        return 0.3 * self.frequency + 0.3 * self.importance + 0.2 * self.novelty + 0.2 * self.durability

    def to_dict(self) -> Dict[str, float]:
        return {
            "frequency": self.frequency, "importance": self.importance,
            "novelty": self.novelty, "durability": self.durability,
            "total": round(self.total, 3),
        }


@dataclass
class ClassificationResult:
    """Classification result for an experience."""
    experience_id: str
    score: ExperienceScore
    should_consolidate: bool
    priority: str  # high, medium, low
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "score": self.score.to_dict(),
            "should_consolidate": self.should_consolidate,
            "priority": self.priority,
            "reason": self.reason,
        }


class ExperienceClassifier:
    """Classify experiences for weight consolidation eligibility.

    Usage:
        classifier = ExperienceClassifier(threshold=0.6)
        result = classifier.classify(experience)
        if result.should_consolidate:
            consolidator.process(experience)
    """

    # Keywords indicating high importance
    IMPORTANCE_KEYWORDS = [
        "critical", "urgent", "must", "important", "breakthrough",
        "critical", "重大", "关键", "必须", "突破",
    ]

    # Keywords indicating durable (long-term) knowledge
    DURABILITY_KEYWORDS = [
        "always", "never", "prefer", "pattern", "rule", "principle",
        "总是", "从不", "偏好", "模式", "规则", "原则",
    ]

    def __init__(self, threshold: float = 0.6, frequency_window: int = 10):
        self.threshold = threshold
        self.frequency_window = frequency_window
        self._seen_patterns: Dict[str, int] = {}  # pattern → count
        self._known_topics: set = set()  # Topics already consolidated

    def classify(self, experience: Dict[str, Any]) -> ClassificationResult:
        """Classify an experience for consolidation.

        Args:
            experience: Experience dict with content, metadata, etc.

        Returns:
            ClassificationResult with score and recommendation
        """
        exp_id = experience.get("id", "unknown")
        content = experience.get("content", "")
        metadata = experience.get("metadata", {})

        if not content:
            return ClassificationResult(
                experience_id=exp_id, score=ExperienceScore(),
                should_consolidate=False, priority="low",
                reason="Empty content",
            )

        score = ExperienceScore()
        content_lower = content.lower()

        # Frequency: check pattern repetition
        patterns = self._extract_patterns(content)
        for pattern in patterns:
            self._seen_patterns[pattern] = self._seen_patterns.get(pattern, 0) + 1
        if patterns:
            avg_freq = sum(self._seen_patterns.get(p, 0) for p in patterns) / len(patterns)
            score.frequency = min(1.0, avg_freq / self.frequency_window)
        else:
            score.frequency = 0.1  # First occurrence

        # Importance: check for importance keywords
        importance_hits = sum(
            1 for kw in self.IMPORTANCE_KEYWORDS if kw in content_lower
        )
        score.importance = min(1.0, importance_hits * 0.3 + 0.2)

        # Novelty: check if topic is new
        topics = self._extract_topics(content)
        new_topics = topics - self._known_topics
        score.novelty = len(new_topics) / max(len(topics), 1) if topics else 0.5
        self._known_topics.update(topics)

        # Durability: check for durability keywords
        durability_hits = sum(
            1 for kw in self.DURABILITY_KEYWORDS if kw in content_lower
        )
        score.durability = min(1.0, durability_hits * 0.3 + 0.1)

        # Classification
        should = score.total >= self.threshold
        if score.total >= 0.8:
            priority = "high"
        elif score.total >= 0.6:
            priority = "medium"
        else:
            priority = "low"

        reason = (
            f"Score={score.total:.2f} (f={score.frequency:.2f} "
            f"i={score.importance:.2f} n={score.novelty:.2f} d={score.durability:.2f})"
        )

        return ClassificationResult(
            experience_id=exp_id, score=score,
            should_consolidate=should, priority=priority, reason=reason,
        )

    def _extract_patterns(self, content: str) -> set:
        """Extract patterns from content."""
        words = re.findall(r"\b\w{4,}\b", content.lower())
        stop = {"this", "that", "with", "from", "have", "been", "when", "they", "them"}
        return {w for w in words if w not in stop}

    def _extract_topics(self, content: str) -> set:
        """Extract topic keywords from content."""
        words = re.findall(r"\b\w{5,}\b", content.lower())
        return set(words)

    def reset(self):
        """Reset classifier state."""
        self._seen_patterns.clear()
        self._known_topics.clear()
