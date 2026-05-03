"""
claw-mem v2.9.1 - Belief Synthesizer

Synthesizes observations into structured beliefs using keyword-based heuristics
(with LLM escalation for complex cases).

Observation → Belief pipeline:
  1. Collect observations from recent memory
  2. Group by topic/pattern
  3. Synthesize into beliefs with confidence scores
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import re


@dataclass
class Observation:
    """An observed fact or event from memory."""
    source: str   # Memory source identifier
    content: str  # The observed content
    timestamp: str = ""
    memory_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source, "content": self.content,
            "timestamp": self.timestamp, "memory_id": self.memory_id,
        }


@dataclass
class Belief:
    """A synthesized belief derived from observations."""
    id: str
    statement: str       # The belief statement
    confidence: float    # 0.0 - 1.0
    observations: List[str] = field(default_factory=list)  # Source observation IDs
    category: str = "general"  # user_preference, fact, pattern, etc.
    created_at: str = ""
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "statement": self.statement,
            "confidence": self.confidence, "category": self.category,
            "version": self.version, "created_at": self.created_at,
        }


@dataclass
class SynthesizerConfig:
    """Configuration for the belief synthesizer."""
    min_observations: int = 2
    min_confidence: float = 0.3
    use_llm: bool = False  # Enable LLM for complex synthesis
    llm_model: str = ""    # Model name if using LLM


class BeliefSynthesizer:
    """Synthesize observations into beliefs.

    Uses pattern-based heuristics for fast synthesis. When enabled,
    escalates complex cases to LLM for deeper analysis.

    Usage:
        synth = BeliefSynthesizer()
        observations = synth.extract_observations(memories)
        beliefs = synth.synthesize(observations, user_id="user123")
    """

    # Patterns for extracting observations from memory content
    OBSERVATION_PATTERNS = [
        (r"User prefers (.+)", "user_preference", 0.8),
        (r"User likes (.+)", "user_preference", 0.8),
        (r"User dislikes (.+)", "user_preference", 0.7),
        (r"User (?:uses|needs|requires|wants) (.+)", "user_fact", 0.6),
        (r"Important: (.+)", "fact", 0.9),
        (r"Learned: (.+)", "fact", 0.8),
        (r"(?:Decided|Resolved): (.+)", "decision", 0.7),
        (r"Error: (.+?)(?:\. |$)", "error_pattern", 0.6),
        (r"(?:Always|Never) (.+)", "pattern", 0.5),
    ]

    def __init__(self, config: Optional[SynthesizerConfig] = None):
        self.config = config or SynthesizerConfig()
        self._belief_counter = 0

    def extract_observations(self, memories: List[Dict[str, Any]]) -> List[Observation]:
        """Extract observations from memory records.

        Args:
            memories: List of memory dicts with content and metadata

        Returns:
            List of extracted observations
        """
        observations: List[Observation] = []

        for mem in memories:
            content = mem.get("content", "")
            if not content:
                continue

            for pattern, category, confidence in self.OBSERVATION_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    observations.append(Observation(
                        source=mem.get("source", "memory"),
                        content=extracted,
                        timestamp=mem.get("timestamp", ""),
                        memory_id=mem.get("id", ""),
                        metadata={
                            "category": category,
                            "extraction_confidence": confidence,
                            "original_content": content,
                        },
                    ))
                    break  # First match only per memory

        return observations

    def synthesize(
        self, observations: List[Observation], user_id: str = "",
    ) -> List[Belief]:
        """Synthesize observations into beliefs.

        Groups observations by topic, merges related observations,
        and produces structured beliefs with confidence scores.

        Args:
            observations: Extracted observations
            user_id: User identifier for the belief

        Returns:
            List of synthesized beliefs
        """
        if len(observations) < self.config.min_observations:
            return []

        beliefs: List[Belief] = []
        topics = self._group_by_topic(observations)

        for topic, obs_list in topics.items():
            if len(obs_list) < self.config.min_observations:
                continue

            # Calculate confidence from observation count and individual confidence
            avg_confidence = sum(
                o.metadata.get("extraction_confidence", 0.5) for o in obs_list
            ) / len(obs_list)

            if avg_confidence < self.config.min_confidence:
                continue

            # Synthesize belief statement
            statement = self._synthesize_statement(topic, obs_list)
            self._belief_counter += 1

            beliefs.append(Belief(
                id=f"BEL_{self._belief_counter:04d}",
                statement=statement,
                confidence=round(avg_confidence, 2),
                observations=[o.memory_id for o in obs_list if o.memory_id],
                category=obs_list[0].metadata.get("category", "general"),
                created_at=datetime.utcnow().isoformat(),
            ))

        return beliefs

    def _group_by_topic(self, observations: List[Observation]) -> Dict[str, List[Observation]]:
        """Group observations by shared topic keywords."""
        topics: Dict[str, List[Observation]] = {}
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "to", "for"}

        for obs in observations:
            # Extract keywords from content
            words = set(w.lower().strip(".,!?;:()[]{}") for w in obs.content.split())
            words = words - stop_words

            # Find best matching topic
            best_topic = None
            best_score = 0
            for topic in topics:
                topic_words = set(topic.split())
                score = len(words & topic_words)
                if score > best_score:
                    best_score = score
                    best_topic = topic

            if best_score >= 1 and best_topic:
                topics[best_topic].append(obs)
            else:
                # New topic: use the longest keyword as topic
                key = sorted(words, key=len, reverse=True)[0] if words else "general"
                topics.setdefault(key, []).append(obs)

        return topics

    def _synthesize_statement(self, topic: str, obs_list: List[Observation]) -> str:
        """Synthesize a belief statement from grouped observations."""
        if not obs_list:
            return f"Observed: {topic}"

        # Use the most confident observation as the base
        best = max(obs_list, key=lambda o: o.metadata.get("extraction_confidence", 0))
        return f"Belief about {topic}: {best.content}"
