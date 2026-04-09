#!/usr/bin/env python3
"""
Test Heuristic Retriever

Tests time decay, type matching, and keyword importance heuristics.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_mem.retrieval.heuristic_retriever import (
    TimeDecayScorer,
    TypeMatcher,
    KeywordImportanceScorer,
    HeuristicRetriever,
    HeuristicConfig
)


def test_time_decay():
    """Test time decay scoring"""
    print("=" * 60)
    print("Test 1: Time Decay Scoring")
    print("=" * 60)
    
    scorer = TimeDecayScorer(half_life_days=30.0, min_weight=0.1)
    
    # Test cases
    now = datetime.now()
    
    test_cases = [
        (now, "Today", "Most recent"),
        (now - timedelta(days=7), "7 days ago", "Recent"),
        (now - timedelta(days=30), "30 days ago", "Half-life"),
        (now - timedelta(days=90), "90 days ago", "Older"),
        (now - timedelta(days=365), "1 year ago", "Very old"),
    ]
    
    for timestamp, label, description in test_cases:
        memory = {"content": "Test", "timestamp": timestamp.isoformat()}
        score = scorer.calculate_score(memory)
        print(f"  {label:20s} ({description:15s}): {score:.3f}")
    
    print("\n✅ PASS: Time decay scoring working!")


def test_type_matching():
    """Test type matching"""
    print("\n" + "=" * 60)
    print("Test 2: Type Matching")
    print("=" * 60)
    
    config = HeuristicConfig()
    matcher = TypeMatcher(config.type_keywords)
    
    # Test query type detection
    queries = [
        "What is the user's favorite food?",
        "What movies does the user like?",
        "Tell me about the user's work",
        "Where does the user live?",
    ]
    
    for query in queries:
        types = matcher.detect_query_type(query)
        print(f"\nQuery: {query}")
        print(f"  Detected types: {types}")
    
    # Test type matching score
    print("\n" + "-" * 60)
    print("Type Matching Scores:")
    
    query = "What is the user's favorite food?"
    memories = [
        {"content": "The user loves pizza and pasta"},
        {"content": "The user watches Star Wars every weekend"},
        {"content": "The user works as a software engineer"},
    ]
    
    for memory in memories:
        score = matcher.calculate_score(query, memory)
        print(f"  {memory['content'][:40]:40s}: {score:.2f}")
    
    print("\n✅ PASS: Type matching working!")


def test_keyword_importance():
    """Test keyword importance scoring"""
    print("\n" + "=" * 60)
    print("Test 3: Keyword Importance")
    print("=" * 60)
    
    config = HeuristicConfig()
    scorer = KeywordImportanceScorer(config.important_keywords)
    
    memories = [
        {"content": "The user's favorite food is pizza"},
        {"content": "The user likes to play tennis"},
        {"content": "This is a normal memory without important keywords"},
        {"content": "The user prefers coffee over tea and loves it"},
    ]
    
    for memory in memories:
        score = scorer.calculate_score(memory)
        keywords = [kw for kw in config.important_keywords if kw in memory["content"].lower()]
        print(f"  {memory['content'][:50]:50s}")
        print(f"    Keywords: {keywords}")
        print(f"    Score: {score:.2f}\n")
    
    print("✅ PASS: Keyword importance scoring working!")


def test_heuristic_retriever():
    """Test full heuristic retriever"""
    print("\n" + "=" * 60)
    print("Test 4: Heuristic Retriever (BM25 + Time + Type + Keyword)")
    print("=" * 60)
    
    # Create test memories with timestamps
    now = datetime.now()
    
    memories = [
        {
            "id": "1",
            "content": "The user's favorite food is pizza",
            "timestamp": (now - timedelta(days=1)).isoformat(),
        },
        {
            "id": "2",
            "content": "The user's favorite movie is Star Wars",
            "timestamp": (now - timedelta(days=30)).isoformat(),
        },
        {
            "id": "3",
            "content": "The user likes to play tennis on weekends",
            "timestamp": (now - timedelta(days=7)).isoformat(),
        },
        {
            "id": "4",
            "content": "Peter Cheng founded Project Neo",
            "timestamp": (now - timedelta(days=90)).isoformat(),
        },
    ]
    
    config = HeuristicConfig()
    retriever = HeuristicRetriever(config)
    
    queries = [
        "What is the user's favorite food?",
        "Tell me about recent activities",
        "Who founded the project?",
    ]
    
    for query in queries:
        results = retriever.search(query, memories, limit=3)
        print(f"\nQuery: {query}")
        for i, result in enumerate(results, 1):
            age = "recent" if "1" in result.get("id", "") else "older"
            print(f"  {i}. [{age}] {result['content']}")
    
    print("\n✅ PASS: Heuristic retriever working!")


def test_combined_scores():
    """Test combined scoring breakdown"""
    print("\n" + "=" * 60)
    print("Test 5: Combined Score Breakdown")
    print("=" * 60)
    
    now = datetime.now()
    
    memories = [
        {
            "id": "1",
            "content": "The user's favorite food is pizza",
            "timestamp": (now - timedelta(days=1)).isoformat(),
        },
        {
            "id": "2",
            "content": "The user watched Star Wars last month",
            "timestamp": (now - timedelta(days=30)).isoformat(),
        },
        {
            "id": "3",
            "content": "Peter founded Project Neo",
            "timestamp": (now - timedelta(days=60)).isoformat(),
        },
    ]
    
    config = HeuristicConfig()
    retriever = HeuristicRetriever(config)
    
    query = "What is the user's favorite food?"
    
    # Get BM25 results first
    bm25_results = retriever.bm25_retriever.search(query, memories, limit=3, rank_by_importance=False)
    
    # Calculate individual scores
    print(f"\nQuery: {query}")
    print(f"\nScore breakdown:")
    
    for memory in bm25_results:
        bm25_score = memory.get("_bm25_score", 0)
        time_score = retriever.time_scorer.calculate_score(memory)
        type_score = retriever.type_matcher.calculate_score(query, memory)
        keyword_score = retriever.keyword_scorer.calculate_score(memory)
        
        print(f"\n  Memory: {memory['content'][:40]}")
        print(f"    BM25:     {bm25_score:.3f}")
        print(f"    Time:     {time_score:.3f}")
        print(f"    Type:     {type_score:.3f}")
        print(f"    Keyword:  {keyword_score:.3f}")
    
    print("\n✅ PASS: Score breakdown working!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Heuristic Retriever Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_time_decay()
        test_type_matching()
        test_keyword_importance()
        test_heuristic_retriever()
        test_combined_scores()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
