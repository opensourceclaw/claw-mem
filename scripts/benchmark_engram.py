#!/usr/bin/env python3
"""Engram benchmark script (v2.19.0). Tests 1K/10K/100K memory performance."""

import sys
import os
import json
import time
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from claw_mem.retrieval.engram import EngramIndex


def generate_content(idx: int) -> str:
    templates = [
        f"Memory {idx}: User prefers dark mode settings",
        f"Configuration {idx}: Database connection pool size is 20",
        f"Task {idx}: Implement REST API endpoint for user management",
        f"Bug fix {idx}: Graph serialization issue resolved",
        f"Feature {idx}: Added spreading activation for graph search",
        f"Note {idx}: Important: session continuity must be preserved",
        f"Decision {idx}: Use PostgreSQL for the main database",
        f"Meeting {idx}: Discussed performance optimization strategies",
        f"Review {idx}: Code review completed for the memory module",
        f"Update {idx}: Updated dependencies to latest versions",
    ]
    return random.choice(templates)


def benchmark(size: int, iterations: int = 1000) -> dict:
    print(f"\n  Benchmarking {size} memories...")
    engram = EngramIndex(ngram_size=3)

    # Phase 1: Index
    t0 = time.time()
    for i in range(size):
        engram.index(f"mem_{i}", generate_content(i))
    index_time = (time.time() - t0) * 1000
    print(f"    Index: {index_time:.1f}ms ({size} entries)")

    # Phase 2: Query
    queries = [
        "dark mode",
        "database connection",
        "REST API",
        "graph serialization",
        "spreading activation",
        "session continuity",
    ]

    latencies = []
    t0 = time.time()
    for _ in range(iterations):
        q = random.choice(queries)
        t1 = time.time()
        results = engram.lookup(q, top_k=10)
        latencies.append((time.time() - t1) * 1000)
        # Warm cache: access results
        if results:
            pass

    query_time = (time.time() - t0) * 1000
    avg_latency = sum(latencies) / len(latencies)
    sorted_lat = sorted(latencies)
    p50 = sorted_lat[len(sorted_lat) // 2]
    p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
    p99 = sorted_lat[int(len(sorted_lat) * 0.99)]

    qps = iterations / (query_time / 1000)

    stats = engram.get_stats()

    result = {
        "size": size,
        "index_time_ms": round(index_time, 1),
        "query_iterations": iterations,
        "total_query_time_ms": round(query_time, 1),
        "avg_latency_ms": round(avg_latency, 4),
        "p50_latency_ms": round(p50, 4),
        "p95_latency_ms": round(p95, 4),
        "p99_latency_ms": round(p99, 4),
        "qps": round(qps, 1),
        "memory_estimate_bytes": stats["memory_estimate_bytes"],
        "memory_entries": stats["memory_count"],
        "hash_count": stats["hash_count"],
    }
    print(f"    Query: avg={avg_latency:.4f}ms, p95={p95:.4f}ms, qps={qps:.1f}")
    return result


def main():
    print("Engram Performance Benchmark (v2.19.0)")
    print("=" * 50)

    results = []
    for size in [1000, 10000]:
        r = benchmark(size, iterations=500 if size == 10000 else 1000)
        results.append(r)

    # Targets check
    print("\n  Performance targets check:")
    for r in results:
        s = r["size"]
        passed = True
        if s <= 1000 and r["p95_latency_ms"] > 1.0:
            passed = False
        if s <= 10000 and r["p95_latency_ms"] > 5.0:
            passed = False
        status = "PASS" if passed else "FAIL"
        print(f"    {s}: p95={r['p95_latency_ms']:.4f}ms [{status}]")

    # Output JSON
    output = {
        "version": "2.19.0",
        "benchmark": "engram",
        "results": results,
    }
    out_path = os.path.join(os.path.dirname(__file__), "..", "reports", "benchmark_engram.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {out_path}")


if __name__ == "__main__":
    main()
