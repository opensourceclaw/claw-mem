#!/usr/bin/env python
"""Performance benchmark for claw-mem v4.5.0 cross-agent memory.

Measures MemoryPool, CrossAgentSync, and AgentAgnosticMemory
operations at 1K, 10K, and 100K record scales.
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from claw_mem.memory.pool import MemoryPool
from claw_mem.memory.sync import CrossAgentSync
from claw_mem.memory.agnostic import AgentAgnosticMemory, MemoryRecord


def percentile(values, p):
    """Compute the p-th percentile of a sorted list."""
    if not values:
        return 0.0
    values.sort()
    k = (len(values) - 1) * p / 100
    f = int(k)
    c = k - f
    if f + 1 < len(values):
        return values[f] + c * (values[f + 1] - values[f])
    return values[f]


def benchmark_operation(name, func, iterations=100):
    """Run func `iterations` times, return stats in ms."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "op": name,
        "iterations": iterations,
        "p50_ms": round(percentile(times, 50), 4),
        "p95_ms": round(percentile(times, 95), 4),
        "min_ms": round(min(times), 4),
        "max_ms": round(max(times), 4),
        "avg_ms": round(sum(times) / len(times), 4),
    }


def bench_memory_pool(n_records):
    """Benchmark MemoryPool with n_records."""
    pool = MemoryPool()
    record = MemoryRecord(
        id="r1", agent_id="a1", memory_type="episodic",
        content="test content", tags=["test"], timestamp=time.time(),
    )

    # Pre-populate
    for i in range(n_records):
        pool.store(MemoryRecord(
            id=f"r{i}", agent_id=f"a{i % 10}", memory_type="episodic",
            content=f"content {i}", tags=["bench"], timestamp=time.time(),
        ))

    results = []

    results.append(benchmark_operation(f"pool.store({n_records})", lambda: pool.store(MemoryRecord(
        id=f"r_new", agent_id="a1", memory_type="episodic",
        content="new content", tags=["bench"], timestamp=time.time(),
    ))))

    results.append(benchmark_operation(f"pool.query({n_records})", lambda: pool.query({"agent_id": "a1"})))

    return results


def bench_sync(n_records):
    """Benchmark CrossAgentSync with n_records."""
    pool = MemoryPool()
    sync = CrossAgentSync(pool=pool)
    record = MemoryRecord(
        id="r1", agent_id="a1", memory_type="episodic",
        content="test", tags=["bench"], timestamp=time.time(),
    )

    # Pre-populate
    for i in range(n_records):
        sync.push(MemoryRecord(
            id=f"r{i}", agent_id="a1", memory_type="episodic",
            content=f"content {i}", tags=["bench"], timestamp=time.time(),
        ), target_agents=["a2"])

    results = []

    results.append(benchmark_operation(f"sync.push({n_records})", lambda: sync.push(
        MemoryRecord(id="r_new", agent_id="a1", memory_type="episodic",
                     content="new", tags=["bench"], timestamp=time.time()),
        target_agents=["a2"],
    )))

    results.append(benchmark_operation(f"sync.pull({n_records})", lambda: sync.pull("a1")))

    return results


def bench_agnostic():
    """Benchmark AgentAgnosticMemory format conversion."""
    results = []
    mem = {"content": "Hello, world!", "tags": ["greeting"], "memory_type": "episodic"}

    results.append(benchmark_operation("to_shared_format", lambda: AgentAgnosticMemory.to_shared_format(mem, "a1")))

    record = AgentAgnosticMemory.to_shared_format(mem, "a1")
    results.append(benchmark_operation("from_shared_format", lambda: AgentAgnosticMemory.from_shared_format(record)))

    return results


def main():
    print("=" * 70)
    print("claw-mem v4.5.0 Performance Benchmark")
    print("=" * 70)

    all_results = []

    # AgentAgnosticMemory benchmarks
    print("\n--- AgentAgnosticMemory ---")
    for r in bench_agnostic():
        all_results.append(r)
        print(f"  {r['op']:30s} p50={r['p50_ms']:>7.3f}ms  p95={r['p95_ms']:>7.3f}ms")

    # MemoryPool benchmarks at different scales
    for n in [1000, 10000, 100000]:
        print(f"\n--- MemoryPool (n={n}) ---")
        for r in bench_memory_pool(n):
            all_results.append(r)
            print(f"  {r['op']:30s} p50={r['p50_ms']:>7.3f}ms  p95={r['p95_ms']:>7.3f}ms")

    # CrossAgentSync benchmarks at different scales
    for n in [1000, 10000, 100000]:
        print(f"\n--- CrossAgentSync (n={n}) ---")
        for r in bench_sync(n):
            all_results.append(r)
            print(f"  {r['op']:30s} p50={r['p50_ms']:>7.3f}ms  p95={r['p95_ms']:>7.3f}ms")

    print("\n" + "=" * 70)
    print("Summary — Target Comparison")
    print("=" * 70)
    targets = {
        "pool.store": (1.0, 3.0),
        "pool.query": (2.0, 5.0),
        "sync.push": (1.0, 3.0),
        "sync.pull": (2.0, 5.0),
        "to_shared_format": (0.1, 0.5),
        "from_shared_format": (0.1, 0.5),
    }
    for r in all_results:
        op_key = r["op"].split("(")[0]
        if op_key in targets:
            t50, t95 = targets[op_key]
            p50_ok = "✓" if r["p50_ms"] < t50 else "✗"
            p95_ok = "✓" if r["p95_ms"] < t95 else "✗"
            print(f"  {r['op']:30s} target(p50<{t50}ms {p50_ok}, p95<{t95}ms {p95_ok})  actual(p50={r['p50_ms']}ms, p95={r['p95_ms']}ms)")

    print("\nBenchmark complete.")


if __name__ == "__main__":
    main()
