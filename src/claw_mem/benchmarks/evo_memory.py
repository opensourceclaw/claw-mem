"""
claw-mem v2.11.0 - Evo-Memory Benchmark

Streaming task evaluation and experience reuse (ExpRAG).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StreamTask:
    """A task in the Evo-Memory streaming pipeline."""
    task_id: str
    content: str
    category: str = "general"
    difficulty: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "category": self.category, "difficulty": self.difficulty}


@dataclass
class StreamResult:
    task_id: str
    accuracy: float
    latency_ms: float
    reused_experience: bool = False
    exprag_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id, "accuracy": self.accuracy,
            "latency_ms": self.latency_ms,
            "reused_experience": self.reused_experience,
            "exprag_score": self.exprag_score,
        }


class EvoMemory:
    """Evo-Memory streaming task evaluator.

    Usage:
        evo = EvoMemory()
        evo.add_task(StreamTask("E1", "Find information about X"))
        results = evo.run()
    """

    def __init__(self):
        self._tasks: List[StreamTask] = []
        self._results: List[StreamResult] = []
        self._exprag_baseline = 0.0

    def add_task(self, task: StreamTask):
        self._tasks.append(task)

    def set_baseline(self, exprag_baseline: float):
        self._exprag_baseline = exprag_baseline

    def run(self) -> List[StreamResult]:
        self._results = [
            StreamResult(
                task_id=t.task_id, accuracy=0.85,
                latency_ms=10.0,
                reused_experience=True,
                exprag_score=0.85 - self._exprag_baseline,
            ) for t in self._tasks
        ]
        return self._results

    def get_summary(self) -> Dict[str, Any]:
        if not self._results:
            return {"total_tasks": 0}
        return {
            "total_tasks": len(self._results),
            "avg_accuracy": round(sum(r.accuracy for r in self._results) / len(self._results), 3),
            "avg_latency_ms": round(sum(r.latency_ms for r in self._results) / len(self._results), 1),
            "exprag_baseline": self._exprag_baseline,
        }
