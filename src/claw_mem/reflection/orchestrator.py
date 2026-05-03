"""
claw-mem v2.9.1 - Reflection Orchestrator

Coordinates the full reflection pipeline:
  1. Collect recent observations from memory
  2. Synthesize into beliefs
  3. Track belief changes
  4. Store results back to memory

Reflection is triggered:
  - On command: memory.reflect()
  - On schedule: automatically when enough new observations accumulate
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .synthesizer import BeliefSynthesizer, Belief, Observation, SynthesizerConfig
from .belief_tracker import BeliefTracker, BeliefVersion


@dataclass
class ReflectionResult:
    """Result of a reflection operation."""
    observations: List[Observation] = field(default_factory=list)
    beliefs: List[Belief] = field(default_factory=list)
    new_beliefs: List[Belief] = field(default_factory=list)
    updated_beliefs: List[Belief] = field(default_factory=list)
    timestamp: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observations_count": len(self.observations),
            "beliefs_total": len(self.beliefs),
            "beliefs_new": len(self.new_beliefs),
            "beliefs_updated": len(self.updated_beliefs),
            "timestamp": self.timestamp,
            "summary": self.summary,
            "observations": [o.to_dict() for o in self.observations[:10]],
            "beliefs": [b.to_dict() for b in self.beliefs[:10]],
        }


class ReflectionOrchestrator:
    """Orchestrate the reflection observation→belief pipeline.

    Usage:
        orch = ReflectionOrchestrator()
        result = orch.reflect(memories, user_id="user123")
        print(f"Synthesized {len(result.beliefs)} beliefs")
    """

    def __init__(self, config: Optional[SynthesizerConfig] = None):
        self.synthesizer = BeliefSynthesizer(config)
        self.tracker = BeliefTracker()
        self._last_reflection_at: Optional[str] = None
        self._reflection_count = 0

    def reflect(
        self, memories: List[Dict[str, Any]], user_id: str = "",
        force: bool = False,
    ) -> ReflectionResult:
        """Execute a full reflection cycle.

        Args:
            memories: Recent memory records to reflect on
            user_id: User identifier
            force: Force reflection even if not enough data

        Returns:
            ReflectionResult with observations and beliefs
        """
        now = datetime.utcnow().isoformat()
        self._reflection_count += 1
        self._last_reflection_at = now

        # Step 1: Extract observations
        observations = self.synthesizer.extract_observations(memories)

        # Step 2: Synthesize beliefs
        beliefs = self.synthesizer.synthesize(observations, user_id)

        # Step 3: Track changes (new vs updated)
        new_beliefs = []
        updated_beliefs = []

        for belief in beliefs:
            existing = self.tracker.get_current(belief.id)
            if existing:
                # Check if actually changed
                if existing.statement != belief.statement:
                    self.tracker.update(belief.id, belief.statement, belief.confidence)
                    updated_beliefs.append(belief)
            else:
                self.tracker.record(belief.id, belief.statement, belief.confidence)
                new_beliefs.append(belief)

        # Step 4: Build summary
        summary = (
            f"Reflection #{self._reflection_count}: "
            f"{len(observations)} observations → "
            f"{len(beliefs)} beliefs "
            f"({len(new_beliefs)} new, {len(updated_beliefs)} updated)"
        )

        return ReflectionResult(
            observations=observations,
            beliefs=beliefs,
            new_beliefs=new_beliefs,
            updated_beliefs=updated_beliefs,
            timestamp=now,
            summary=summary,
        )

    def get_beliefs(self, include_history: bool = False) -> List[Dict[str, Any]]:
        """Get all current beliefs.

        Args:
            include_history: Include version history

        Returns:
            List of belief dicts
        """
        beliefs = []
        for belief_id in self.tracker.get_all_ids():
            version = self.tracker.get_current(belief_id)
            if version:
                b = version.to_dict()
                if include_history:
                    b["history"] = [v.to_dict() for v in self.tracker.get_history(belief_id)]
                beliefs.append(b)
        return beliefs

    def get_reflection_stats(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        return {
            "reflection_count": self._reflection_count,
            "last_reflection_at": self._last_reflection_at,
            "total_beliefs": len(self.tracker._store),
            "total_versions": sum(
                len(v) for v in self.tracker._store.values()
            ),
        }
