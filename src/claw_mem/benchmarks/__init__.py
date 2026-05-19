# claw-mem v2.11.0 - Benchmark Evaluation Module
#
# Standardized benchmark framework based on:
#   - MemoryArena (arXiv:2602.16313)
#   - MemBench (arXiv:2506.21605)
#   - Evo-Memory

from .evo_memory import EvoMemory, StreamTask
from .membench import MemBench, MemBenchConfig
from .memory_arena import ArenaTask, ArenaTaskType, MemoryArena
from .metrics import MRR, Accuracy, EvalResult, EvaluationMetrics, Precision, RecallAtK
from .runner import BenchmarkReport, BenchmarkRunner

__all__ = [
    "RecallAtK",
    "MRR",
    "Precision",
    "Accuracy",
    "EvalResult",
    "EvaluationMetrics",
    "MemBench",
    "MemBenchConfig",
    "MemoryArena",
    "ArenaTask",
    "ArenaTaskType",
    "EvoMemory",
    "StreamTask",
    "BenchmarkRunner",
    "BenchmarkReport",
]
