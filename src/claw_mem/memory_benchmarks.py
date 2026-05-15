"""Benchmark Runner — LOCOMO + LongMemEval for claw-mem v2.15.0."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    total_queries: int = 0
    passed: int = 0
    accuracy: float = 0.0
    avg_latency_ms: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)


class BenchmarkRunner:
    """Runs LOCOMO and LongMemEval memory benchmarks.

    LOCOMO: Long Context Memory evaluation (retrieval from long dialogues)
    LongMemEval: Four-capability memory assessment (information extraction,
                 multi-session reasoning, temporal reasoning, knowledge updating)
    """

    def __init__(self):
        self._results: List[BenchmarkResult] = []

    def run_locom(
        self,
        search_fn: Callable[[str, int], List[Dict]],
        test_cases: Optional[List[Dict]] = None,
    ) -> BenchmarkResult:
        """Run LOCOMO benchmark: long dialogue memory retrieval."""
        if test_cases is None:
            test_cases = self._default_locom_cases()

        result = BenchmarkResult(name="LOCOMO", total_queries=len(test_cases))
        for tc in test_cases:
            t0 = time.perf_counter()
            results = search_fn(tc["query"], tc.get("top_k", 10))
            elapsed = (time.perf_counter() - t0) * 1000

            # Check if expected content was found
            found = any(tc["expected"].lower() in str(r.get("text", "")).lower() for r in results)
            if found:
                result.passed += 1

            result.details.append(
                {
                    "query": tc["query"],
                    "found": found,
                    "latency_ms": round(elapsed, 3),
                    "results_count": len(results),
                }
            )

        result.accuracy = round(result.passed / max(1, result.total_queries), 4)
        if result.details:
            result.avg_latency_ms = round(
                sum(d["latency_ms"] for d in result.details) / len(result.details), 2
            )
        logger.info(
            "LOCOMO: %.1f%% accuracy, %.2fms avg", result.accuracy * 100, result.avg_latency_ms
        )
        self._results.append(result)
        return result

    def run_longmem_eval(
        self,
        search_fn: Callable[[str, int], List[Dict]],
        test_cases: Optional[List[Dict]] = None,
    ) -> BenchmarkResult:
        """Run LongMemEval: four-capability assessment."""
        if test_cases is None:
            test_cases = self._default_longmem_cases()

        result = BenchmarkResult(name="LongMemEval", total_queries=len(test_cases))
        capabilities = {"ie": 0, "mr": 0, "tr": 0, "ku": 0}
        cap_total = {"ie": 0, "mr": 0, "tr": 0, "ku": 0}

        for tc in test_cases:
            t0 = time.perf_counter()
            results = search_fn(tc["query"], tc.get("top_k", 10))
            elapsed = (time.perf_counter() - t0) * 1000

            found = any(tc["expected"].lower() in str(r.get("text", "")).lower() for r in results)
            if found:
                result.passed += 1
                cap = tc.get("capability", "ie")
                capabilities[cap] += 1
            cap_total[tc.get("capability", "ie")] += 1

            result.details.append(
                {
                    "query": tc["query"],
                    "found": found,
                    "capability": tc.get("capability", ""),
                    "latency_ms": round(elapsed, 3),
                }
            )

        result.accuracy = round(result.passed / max(1, result.total_queries), 4)
        if result.details:
            result.avg_latency_ms = round(
                sum(d["latency_ms"] for d in result.details) / len(result.details), 2
            )

        # Per-capability breakdown
        for cap in capabilities:
            n = cap_total[cap]
            if n > 0:
                logger.info("  %s: %d/%d", cap, capabilities[cap], n)

        logger.info("LongMemEval: %.1f%% accuracy", result.accuracy * 100)
        self._results.append(result)
        return result

    def _default_locom_cases(self) -> List[Dict]:
        return [
            {"query": "project status update", "expected": "memory", "top_k": 10},
            {"query": "bug fix deployment", "expected": "test", "top_k": 10},
            {"query": "performance optimization", "expected": "index", "top_k": 10},
            {"query": "version release notes", "expected": "release", "top_k": 10},
            {"query": "architecture review feedback", "expected": "design", "top_k": 10},
        ]

    def _default_longmem_cases(self) -> List[Dict]:
        return [
            {"query": "key features implemented", "expected": "graph", "capability": "ie"},
            {"query": "cross session follow-up decision", "expected": "test", "capability": "mr"},
            {"query": "event timeline order", "expected": "release", "capability": "tr"},
            {"query": "updated project requirements", "expected": "version", "capability": "ku"},
        ]

    def get_latest(self) -> Optional[BenchmarkResult]:
        return self._results[-1] if self._results else None
