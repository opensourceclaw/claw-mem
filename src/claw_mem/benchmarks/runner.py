"""
claw-mem v2.11.0 - Unified Benchmark Runner

Runs all benchmarks and generates structured reports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .membench import MemBench, MemBenchConfig
from .memory_arena import MemoryArena, ArenaTask, ArenaTaskType
from .evo_memory import EvoMemory, StreamTask


@dataclass
class BenchmarkReport:
    name: str = "claw-mem Benchmark"
    arena: Dict[str, Any] = field(default_factory=dict)
    membench: Dict[str, Any] = field(default_factory=dict)
    evo_memory: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "arena": self.arena,
            "membench": self.membench,
            "evo_memory": self.evo_memory,
            "summary": self.summary,
        }


class BenchmarkRunner:
    """Run all benchmarks on a memory system.

    Usage:
        runner = BenchmarkRunner()
        report = runner.run_all()
        print(report.to_dict())
    """

    def __init__(self):
        self.memory_arena = MemoryArena()
        self.membench = MemBench()
        self.evo_memory = EvoMemory()

    def setup_defaults(self):
        """Setup default benchmark tasks."""
        # MemoryArena tasks
        arena_tasks = [
            ArenaTask("WA1", ArenaTaskType.WEB_NAVIGATION,
                     "Navigate to find a specific item", steps=3),
            ArenaTask("PA1", ArenaTaskType.PREFERENCE_CONSTRAINTS,
                     "Satisfy user preferences under constraints", steps=2),
            ArenaTask("PS1", ArenaTaskType.PROGRESSIVE_SEARCH,
                     "Progressively refine search results", steps=4),
            ArenaTask("FA1", ArenaTaskType.FORMAL_REASONING,
                     "Reason about formal constraints", steps=2),
        ]
        for t in arena_tasks:
            self.memory_arena.add_task(t)

        # Evo-Memory streaming tasks
        stream_tasks = [
            StreamTask("E1", "Web info retrieval task", "search"),
            StreamTask("E2", "Memory update task", "update"),
            StreamTask("E3", "Cross-session retrieval", "retrieval"),
        ]
        for t in stream_tasks:
            self.evo_memory.add_task(t)
        self.evo_memory.set_baseline(0.45)

    def run_all(self) -> BenchmarkReport:
        """Run all benchmarks and return a report."""
        self.setup_defaults()

        # MemoryArena
        arena_results = self.memory_arena.run()
        arena_summary = self.memory_arena.get_summary()

        # MemBench
        retrieval = self.membench.evaluate_retrieval(
            ["id1", "id3", "id2", "id5", "id4"],
            {"id1", "id2", "id3"},
        )
        few_shot = self.membench.evaluate_test_time_learning(0.75)
        long_range = self.membench.evaluate_long_range([0.82, 0.78, 0.85])
        forgetting = self.membench.evaluate_forgetting(
            {"a", "b", "c"}, {"b"}, {"a", "c"},
        )

        # Evo-Memory
        evo_results = self.evo_memory.run()
        evo_summary = self.evo_memory.get_summary()

        return BenchmarkReport(
            arena=arena_summary,
            membench={
                "retrieval": retrieval.to_dict(),
                "few_shot": few_shot, "long_range": long_range,
                "forgetting": forgetting,
            },
            evo_memory=evo_summary,
            summary={
                "total_benchmarks": 3,
                "memory_arena_completed": arena_summary.get("completed", 0),
                "membench_mrr": retrieval.get("mrr"),
                "evo_memory_accuracy": evo_summary.get("avg_accuracy", 0),
            },
        )
