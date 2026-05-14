"""Ground Truth Store — raw episodic storage with fact extraction."""

import logging
import re
import time
import uuid
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GroundTruthStore:
    """Raw episodic storage for truth preservation and fact verification."""

    def __init__(self):
        self._episodes: List[Dict] = []
        self._facts: List[Dict] = []

    def store_episode(
        self, text: str, metadata: Optional[Dict] = None
    ) -> str:
        """Store a raw conversation as ground truth."""
        eid = str(uuid.uuid4())
        episode = {
            "id": eid,
            "text": text,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self._episodes.append(episode)
        logger.debug("Episode stored: %s", eid[:8])
        return eid

    def store_fact(
        self, fact: str, source_episode_id: str
    ) -> str:
        """Store an extracted fact linked to its source episode."""
        fid = str(uuid.uuid4())
        self._facts.append({
            "id": fid,
            "fact": fact,
            "source_episode_id": source_episode_id,
            "timestamp": time.time(),
        })
        return fid

    def extract_facts(self, text: str) -> List[str]:
        """Extract factual statements from text using pattern matching."""
        facts = []
        sentences = re.split(r"[.!?。！？\n]+", str(text))
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # Pattern 1: "X is Y" or "X was Y"
            if re.search(r"\b(is|was|are|were)\b", sentence, re.IGNORECASE):
                facts.append(sentence)

            # Pattern 2: "X did Y" (action statements)
            elif re.search(r"\b(implemented|fixed|added|created|removed|updated|changed)\b", sentence, re.IGNORECASE):
                facts.append(sentence)

            # Pattern 3: Numbers with units (measurements)
            elif re.search(r"\d+[%kmsMBGT]", sentence):
                facts.append(sentence)

        return list(set(facts))

    def verify_fact(self, fact_id: str) -> bool:
        """Check if a fact is still consistent with source episodes."""
        fact = next((f for f in self._facts if f["id"] == fact_id), None)
        if not fact:
            return False
        source = next(
            (e for e in self._episodes if e["id"] == fact["source_episode_id"]),
            None,
        )
        if not source:
            return False
        return fact["fact"].lower() in source["text"].lower()

    def get_episodes(
        self, limit: int = 10, before: Optional[float] = None
    ) -> List[Dict]:
        """Get recent episodes."""
        episodes = self._episodes
        if before is not None:
            episodes = [e for e in episodes if e["timestamp"] < before]
        return episodes[-limit:]

    def get_facts(self, limit: int = 20) -> List[Dict]:
        """Get most recent facts."""
        return self._facts[-limit:]

    def count_episodes(self) -> int:
        return len(self._episodes)

    def count_facts(self) -> int:
        return len(self._facts)
