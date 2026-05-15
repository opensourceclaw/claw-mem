#!/usr/bin/env python3
"""
P0 Metrics Benchmark Script

Validates three P0 metric targets:
1. Retrieval Hit Rate (> 91%)
2. Injection Relevance (> 80%)
3. RL Accuracy (> 90%)

Generates synthetic test data and runs benchmarks.
"""

import sys
import os
import time
import json
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ── Test Data Generation ──────────────────────────────────────────────────────


def generate_retrieval_test_data(n: int = 120) -> list:
    """Generate retrieval test dataset."""
    domains = [
        ("Python", "performance", "optimization"),
        ("JavaScript", "frontend", "React"),
        ("Docker", "deployment", "container"),
        ("AI", "machine learning", "neural network"),
        ("database", "SQL", "indexing"),
        ("git", "version control", "branch"),
        ("API", "REST", "endpoint"),
        ("testing", "unit test", "coverage"),
    ]

    memories = []
    queries = []
    memory_id = 0

    for domain, topic1, topic2 in domains:
        for i in range(3):
            memory_id += 1
            mem = {
                "id": f"mem_{memory_id:03d}",
                "content": f"Discussion about {domain} {topic1} {topic2} techniques - iteration {i+1}",
                "timestamp": f"2025-05-{(memory_id % 28)+1:02d}T10:00:00",
                "tags": [domain.lower(), topic1, topic2],
                "memory_type": "semantic",
                "access_count": random.randint(1, 20),
            }
            memories.append(mem)

        # Generate exact match queries
        queries.append(
            {
                "query": f"what did we discuss about {domain} {topic1}?",
                "expected_memory_ids": [
                    f"mem_{(memory_id-2):03d}",
                    f"mem_{(memory_id-1):03d}",
                    f"mem_{memory_id:03d}",
                ],
                "domain": domain,
            }
        )

    # Generate more queries with synonyms
    synonyms = [
        ("optimization", "performance tuning", "speed improvement"),
        ("deployment", "release", "publishing"),
        ("testing", "verification", "validation"),
        ("machine learning", "ML", "AI training"),
    ]

    for original, syn1, syn2 in synonyms:
        memory_id += 1
        mem = {
            "id": f"mem_{memory_id:03d}",
            "content": f"Notes on {original} strategies and {syn2} methods",
            "timestamp": f"2025-05-{random.randint(1,28):02d}T10:00:00",
            "tags": [original, syn1],
            "memory_type": "semantic",
            "access_count": random.randint(1, 15),
        }
        memories.append(mem)

        queries.append(
            {
                "query": f"tell me about {syn1} strategies",
                "expected_memory_ids": [f"mem_{memory_id:03d}"],
                "domain": original,
            }
        )

    return memories, queries


def generate_injection_test_data(n: int = 60) -> list:
    """Generate injection relevance test scenarios."""
    contexts = [
        "User is discussing Python project development and performance optimization",
        "User wants to set up a Docker deployment pipeline",
        "User is reviewing code quality and asking about testing best practices",
        "User is planning the weekly sprint retrospective",
        "User is working on API design and REST endpoint structure",
        "User is troubleshooting database query performance",
        "User is setting up a CI/CD pipeline for automated testing",
        "User is researching machine learning model deployment strategies",
        "User is doing code review for a pull request",
        "User is writing project documentation and API docs",
    ]

    memory_pool = [
        {
            "id": "py_perf",
            "content": "Python performance optimization: use list comprehensions, caching with functools.lru_cache, and profile with cProfile",
            "memory_type": "procedural",
        },
        {
            "id": "py_project",
            "content": "Python project structure: src/ layout, pyproject.toml configuration, pytest for testing",
            "memory_type": "semantic",
        },
        {
            "id": "docker_deploy",
            "content": "Docker deployment: multi-stage builds, docker-compose for services, healthcheck configuration",
            "memory_type": "procedural",
        },
        {
            "id": "docker_network",
            "content": "Docker networking: bridge networks, port mapping, service discovery via DNS",
            "memory_type": "semantic",
        },
        {
            "id": "test_pytest",
            "content": "Testing with pytest: fixtures, parametrize, coverage reports, mock objects",
            "memory_type": "procedural",
        },
        {
            "id": "test_coverage",
            "content": "Test coverage targets: 80% line coverage minimum, branch coverage tracking, mutation testing",
            "memory_type": "semantic",
        },
        {
            "id": "sprint_review",
            "content": "Sprint retrospective format: what went well, what to improve, action items for next sprint",
            "memory_type": "procedural",
        },
        {
            "id": "api_design",
            "content": "REST API design: resource naming, HTTP verbs, pagination, error response format",
            "memory_type": "procedural",
        },
        {
            "id": "api_auth",
            "content": "API authentication: JWT tokens, OAuth2 flow, rate limiting middleware",
            "memory_type": "semantic",
        },
        {
            "id": "db_index",
            "content": "Database indexing strategies: B-tree for equality, bitmap for low-cardinality, covering indexes",
            "memory_type": "procedural",
        },
        {
            "id": "db_query",
            "content": "Query optimization: EXPLAIN ANALYZE, query plan analysis, avoiding N+1 queries",
            "memory_type": "semantic",
        },
        {
            "id": "cicd_pipeline",
            "content": "CI/CD pipeline: GitHub Actions workflow, build-test-deploy stages, environment configuration",
            "memory_type": "procedural",
        },
        {
            "id": "ml_deploy",
            "content": "ML model deployment: model serving with FastAPI, versioning with MLflow, A/B testing",
            "memory_type": "procedural",
        },
        {
            "id": "code_review",
            "content": "Code review checklist: naming conventions, error handling, test coverage, performance implications",
            "memory_type": "procedural",
        },
        {
            "id": "docs_write",
            "content": "Documentation guidelines: docstrings, README structure, API reference, changelog format",
            "memory_type": "procedural",
        },
    ]

    scenarios = []
    for ctx in contexts:
        relevant_ids = []
        ctx_lower = ctx.lower()

        # Match context keywords to memory pool
        if "python" in ctx_lower:
            relevant_ids.extend(["py_perf", "py_project"])
        if "docker" in ctx_lower:
            relevant_ids.extend(["docker_deploy", "docker_network"])
        if "test" in ctx_lower:
            relevant_ids.extend(["test_pytest", "test_coverage"])
        if "sprint" in ctx_lower or "retrospect" in ctx_lower:
            relevant_ids.append("sprint_review")
        if "api" in ctx_lower:
            relevant_ids.extend(["api_design", "api_auth"])
        if "database" in ctx_lower or "query" in ctx_lower:
            relevant_ids.extend(["db_index", "db_query"])
        if "ci/cd" in ctx_lower or "pipeline" in ctx_lower:
            relevant_ids.append("cicd_pipeline")
        if "machine learning" in ctx_lower or "model" in ctx_lower:
            relevant_ids.append("ml_deploy")
        if "code review" in ctx_lower or "pull request" in ctx_lower:
            relevant_ids.append("code_review")
        if "document" in ctx_lower or "docs" in ctx_lower:
            relevant_ids.append("docs_write")

        scenarios.append(
            {
                "context": ctx,
                "relevant_memory_ids": relevant_ids,
                "memory_pool": memory_pool,
            }
        )

    return scenarios


def generate_rl_test_data(n: int = 200) -> list:
    """Generate RL accuracy test data."""
    positive_feedbacks = [
        "thanks, great work!",
        "perfect, exactly what I needed",
        "很好，谢谢！",
        "that's correct, well done",
        "awesome, this solves the problem",
        "good job, I like the solution",
        "thanks for the help, works perfectly",
        "excellent analysis, very thorough",
        "太棒了，完美解决了",
        "right, that makes sense now",
        "got it, thanks for explaining",
        "nice, that's helpful",
        "cool, I understand now",
        "this is exactly right",
        "解决了，感谢",
    ]

    negative_feedbacks = [
        "this is wrong, please fix",
        "incorrect, you misunderstood",
        "不对，搞错了",
        "there's a bug in this code",
        "this doesn't solve the problem",
        "you made an error here",
        "错了，重新来",
        "that's not what I asked for",
        "this has a mistake",
        "请不要这样做",
        "avoid using globals",
        "this is incorrect syntax",
        "should not use deprecated API",
        "never hardcode credentials",
        "bad approach, try again",
    ]

    neutral_feedbacks = [
        "the weather is nice today",
        "what day is it?",
        "can you explain this concept?",
        "how does this algorithm work?",
        "please show me the documentation",
        "list all files in this directory",
        "tell me about the project structure",
        "who created this function?",
    ]

    test_data = []

    for feedback in random.choices(positive_feedbacks, k=n // 3):
        test_data.append({"feedback": feedback, "expected": "positive"})

    for feedback in random.choices(negative_feedbacks, k=n // 3):
        test_data.append({"feedback": feedback, "expected": "negative"})

    for feedback in random.choices(neutral_feedbacks, k=n - len(test_data)):
        test_data.append({"feedback": feedback, "expected": "neutral"})

    random.shuffle(test_data)
    return test_data[:n]


# ── Benchmark Runners ──────────────────────────────────────────────────────────


def benchmark_retrieval_hit_rate() -> dict:
    """Benchmark retrieval hit rate."""
    from claw_mem.retrieval.query_understanding import QueryUnderstanding
    from claw_mem.retrieval.multi_strategy_retriever import MultiStrategyRetriever

    memories, queries = generate_retrieval_test_data(120)
    qu = QueryUnderstanding()
    retriever = MultiStrategyRetriever()

    hits = 0
    total = len(queries)
    details = []

    t0 = time.perf_counter()

    for test in queries:
        expanded = qu.understand(test["query"])
        result = retriever.retrieve(expanded, memories, top_k=10)

        expected_ids = set(test["expected_memory_ids"])
        found_ids = {c.memory_id for c in result.candidates[:10]}

        matched = len(expected_ids & found_ids) > 0
        if matched:
            hits += 1

        details.append(
            {
                "query": test["query"],
                "hit": matched,
                "expected": list(expected_ids),
                "found": list(found_ids)[:5],
                "match_count": len(expected_ids & found_ids),
            }
        )

    elapsed = (time.perf_counter() - t0) * 1000
    hit_rate = hits / total if total > 0 else 0

    return {
        "metric": "retrieval_hit_rate",
        "target": 0.91,
        "actual": round(hit_rate, 4),
        "passed": hit_rate >= 0.91,
        "total_queries": total,
        "hits": hits,
        "misses": total - hits,
        "elapsed_ms": round(elapsed, 1),
        "details": details[:10],  # First 10 for report
    }


def benchmark_injection_relevance() -> dict:
    """Benchmark injection relevance."""
    from claw_mem.proactive_injection import RelevanceScorer, ScoredMemory, ConversationContext

    scenarios = generate_injection_test_data(60)
    scorer = RelevanceScorer()

    correct = 0
    total = len(scenarios)
    details = []

    t0 = time.perf_counter()

    for scenario in scenarios:
        # Create conversation context for scoring
        context = ConversationContext(current_message=scenario["context"])

        # Score all memories against the context
        scored_memories = []
        for mem in scenario["memory_pool"]:
            scored = ScoredMemory(
                memory_id=mem["id"],
                content=mem["content"],
                score=0.0,
                memory_type=mem["memory_type"],
            )
            scored.score = scorer.score(scored, context)
            scored_memories.append(scored)

        # Get top 5 by relevance
        scored_memories.sort(key=lambda m: m.score, reverse=True)
        top_ids = {m.memory_id for m in scored_memories[:5]}
        relevant_ids = set(scenario["relevant_memory_ids"])

        overlap = len(top_ids & relevant_ids)
        is_relevant = overlap > 0
        if is_relevant:
            correct += 1

        details.append(
            {
                "context": scenario["context"][:60],
                "relevant": is_relevant,
                "overlap_count": overlap,
                "top_memories": list(top_ids)[:3],
            }
        )

    elapsed = (time.perf_counter() - t0) * 1000
    relevance_rate = correct / total if total > 0 else 0

    return {
        "metric": "injection_relevance",
        "target": 0.80,
        "actual": round(relevance_rate, 4),
        "passed": relevance_rate >= 0.80,
        "total_scenarios": total,
        "correct": correct,
        "incorrect": total - correct,
        "elapsed_ms": round(elapsed, 1),
        "details": details[:10],
    }


def benchmark_rl_accuracy() -> dict:
    """Benchmark RL classification accuracy."""
    from claw_rl.feedback.enhanced_binary_rl import EnhancedBinaryRLJudge

    test_data = generate_rl_test_data(200)
    judge = EnhancedBinaryRLJudge()

    correct = 0
    total = len(test_data)
    details = []

    t0 = time.perf_counter()

    for test in test_data:
        result = judge.judge(test["feedback"])
        predicted = (
            "positive" if result.reward > 0 else ("negative" if result.reward < 0 else "neutral")
        )
        expected = test["expected"]

        is_correct = predicted == expected
        if is_correct:
            correct += 1

        details.append(
            {
                "feedback": test["feedback"][:50],
                "expected": expected,
                "predicted": predicted,
                "correct": is_correct,
                "confidence": round(result.confidence, 3),
            }
        )

    elapsed = (time.perf_counter() - t0) * 1000
    accuracy = correct / total if total > 0 else 0

    return {
        "metric": "rl_accuracy",
        "target": 0.90,
        "actual": round(accuracy, 4),
        "passed": accuracy >= 0.90,
        "total_samples": total,
        "correct": correct,
        "incorrect": total - correct,
        "elapsed_ms": round(elapsed, 1),
        "details": details[:10],
    }


# ── Main ───────────────────────────────────────────────────────────────────────


def run_all_benchmarks():
    """Run all three benchmarks and generate report."""
    print("=" * 60)
    print("  P0 Metrics Benchmark")
    print("=" * 60)
    print()

    results = []

    print("1. Retrieval Hit Rate Benchmark...")
    r1 = benchmark_retrieval_hit_rate()
    results.append(r1)
    print(
        f"   Hit Rate: {r1['actual']:.2%} (target: >{r1['target']:.0%})  {'PASS' if r1['passed'] else 'FAIL'}"
    )
    print()

    print("2. Injection Relevance Benchmark...")
    r2 = benchmark_injection_relevance()
    results.append(r2)
    print(
        f"   Relevance: {r2['actual']:.2%} (target: >{r2['target']:.0%})  {'PASS' if r2['passed'] else 'FAIL'}"
    )
    print()

    print("3. RL Accuracy Benchmark...")
    r3 = benchmark_rl_accuracy()
    results.append(r3)
    print(
        f"   Accuracy: {r3['actual']:.2%} (target: >{r3['target']:.0%})  {'PASS' if r3['passed'] else 'FAIL'}"
    )
    print()

    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print()
    print(f"{'Metric':<25} {'Target':>8} {'Actual':>8} {'Status':>8}")
    print("-" * 55)

    all_passed = True
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(f"{r['metric']:<25} {r['target']:>7.0%} {r['actual']:>7.1%} {status:>8}")

    print()
    if all_passed:
        print("All benchmarks PASSED!")
    else:
        print("Some benchmarks FAILED. Review details above.")

    # Save results
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "benchmark", "2026-05-15-p0-metrics.json"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport saved to {report_path}")

    return results


if __name__ == "__main__":
    run_all_benchmarks()
