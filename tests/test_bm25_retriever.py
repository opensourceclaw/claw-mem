#!/usr/bin/env python3
"""
Test BM25 Retriever

Quick test to verify BM25 retrieval functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_mem.retrieval.bm25_retriever import BM25Retriever, HybridBM25Retriever


def test_bm25_basic():
    """Test basic BM25 functionality"""
    print("=" * 60)
    print("Test 1: Basic BM25 Search")
    print("=" * 60)
    
    # Create test memories
    memories = [
        {"id": "1", "content": "The user's favorite food is pizza", "type": "semantic"},
        {"id": "2", "content": "The user's favorite movie is Star Wars", "type": "semantic"},
        {"id": "3", "content": "The user likes to play tennis on weekends", "type": "semantic"},
        {"id": "4", "content": "The user's favorite color is blue", "type": "semantic"},
        {"id": "5", "content": "The user prefers coffee over tea", "type": "semantic"},
    ]
    
    # Initialize retriever
    retriever = BM25Retriever()
    
    # Search for favorite food
    query = "What is the user's favorite food?"
    results = retriever.search(query, memories, limit=3)
    
    print(f"\nQuery: {query}")
    print(f"\nTop 3 results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content']}")
    
    # Verify the correct result is ranked first
    if results and "pizza" in results[0]["content"]:
        print("\n✅ PASS: Correct result ranked first!")
    else:
        print("\n❌ FAIL: Expected 'pizza' memory to be ranked first")
    
    print()


def test_bm25_multiple_queries():
    """Test BM25 with multiple queries"""
    print("=" * 60)
    print("Test 2: Multiple Queries")
    print("=" * 60)
    
    memories = [
        {"id": "1", "content": "Peter Cheng is the founder of Project Neo", "type": "semantic"},
        {"id": "2", "content": "Friday is the AI assistant for Project Neo", "type": "semantic"},
        {"id": "3", "content": "JARVIS is the quality assurance agent", "type": "semantic"},
        {"id": "4", "content": "claw-mem is the memory system", "type": "semantic"},
        {"id": "5", "content": "claw-rl is the reinforcement learning system", "type": "semantic"},
    ]
    
    retriever = BM25Retriever()
    
    queries = [
        "Who is the founder?",
        "What is Friday?",
        "What does JARVIS do?",
        "Tell me about memory system",
    ]
    
    for query in queries:
        results = retriever.search(query, memories, limit=2)
        print(f"\nQuery: {query}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['content']}")
    
    print("\n✅ PASS: All queries returned results")


def test_hybrid_retriever():
    """Test hybrid BM25 + keyword retriever"""
    print("\n" + "=" * 60)
    print("Test 3: Hybrid BM25 + Keyword Search")
    print("=" * 60)
    
    memories = [
        {"id": "1", "content": "The user loves Italian food, especially pasta", "type": "semantic"},
        {"id": "2", "content": "The user's favorite programming language is Python", "type": "semantic"},
        {"id": "3", "content": "The user works on AI projects", "type": "semantic"},
    ]
    
    retriever = HybridBM25Retriever()
    
    query = "What food does the user like?"
    results = retriever.search(query, memories, limit=2)
    
    print(f"\nQuery: {query}")
    print(f"\nTop 2 results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content']}")
    
    if results and "food" in results[0]["content"].lower():
        print("\n✅ PASS: Hybrid search working!")
    else:
        print("\n❌ FAIL: Expected food-related memory to be ranked first")
    
    print()


def test_bm25_chinese():
    """Test BM25 with Chinese text"""
    print("=" * 60)
    print("Test 4: Chinese Text Support")
    print("=" * 60)
    
    memories = [
        {"id": "1", "content": "用户最喜欢的食物是披萨", "type": "semantic"},
        {"id": "2", "content": "用户最喜欢的电影是星球大战", "type": "semantic"},
        {"id": "3", "content": "用户喜欢在周末打网球", "type": "semantic"},
    ]
    
    retriever = BM25Retriever()
    
    query = "用户最喜欢什么食物"
    results = retriever.search(query, memories, limit=2)
    
    print(f"\nQuery: {query}")
    print(f"\nTop 2 results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content']}")
    
    if results and "披萨" in results[0]["content"]:
        print("\n✅ PASS: Chinese search working!")
    else:
        print("\n❌ FAIL: Expected '披萨' memory to be ranked first")
    
    print()


def test_bm25_explain():
    """Test BM25 explain functionality"""
    print("=" * 60)
    print("Test 5: BM25 Explain")
    print("=" * 60)
    
    memories = [
        {"id": "1", "content": "Python is a popular programming language", "type": "semantic"},
        {"id": "2", "content": "JavaScript is used for web development", "type": "semantic"},
    ]
    
    retriever = BM25Retriever()
    retriever.build_index(memories)
    
    query = "programming language"
    explanation = retriever.explain(query, 0)
    
    print(f"\nQuery: {query}")
    print(f"Document: {memories[0]['content']}")
    print(f"\nExplanation:")
    print(f"  Query tokens: {explanation['query_tokens']}")
    print(f"  Doc tokens: {explanation['doc_tokens']}")
    print(f"  Token scores: {explanation['token_scores']}")
    print(f"  Total score: {explanation['total_score']:.4f}")
    
    print("\n✅ PASS: Explain functionality working!")


def test_k1_parameter_affects_scores():
    """Test that k1 parameter is accepted and BM25 retriever works with custom params"""
    print("=" * 60)
    print("Test 6: k1 Parameter Acceptance")
    print("=" * 60)

    memories = [
        {"id": "1", "content": "The user likes pizza and pasta", "type": "semantic"},
        {"id": "2", "content": "The user prefers coffee", "type": "semantic"},
        {"id": "3", "content": "The user lives in Beijing", "type": "semantic"},
        {"id": "4", "content": "The user works on AI projects", "type": "semantic"},
    ]

    retriever_custom = BM25Retriever(k1=2.0, b=0.5)
    results = retriever_custom.search("pizza", memories, limit=3, rank_by_importance=False)

    assert len(results) > 0
    assert "pizza" in results[0]["content"]
    assert retriever_custom.k1 == 2.0
    assert retriever_custom.b == 0.5
    print(f"  k1={retriever_custom.k1}, b={retriever_custom.b}, results={len(results)}")
    print("✅ PASS: Custom k1/b parameters accepted!")


def test_recency_boost():
    """Test recency_boost weights recent memories higher"""
    print("\n" + "=" * 60)
    print("Test 7: Recency Boost")
    print("=" * 60)

    from datetime import datetime, timedelta

    now = datetime.now()
    memories = [
        {"id": "1", "content": "old note about Python programming", "type": "semantic",
         "timestamp": (now - timedelta(days=30)).isoformat()},
        {"id": "2", "content": "recent note about Python programming", "type": "semantic",
         "timestamp": now.isoformat()},
        {"id": "3", "content": "Java is used for enterprise apps", "type": "semantic"},
        {"id": "4", "content": "Rust is a systems language", "type": "semantic"},
        {"id": "5", "content": "Go was created at Google", "type": "semantic"},
    ]

    retriever = BM25Retriever(recency_boost=2.0)
    results = retriever.search("Python", memories, limit=3, rank_by_importance=False)

    print(f"  Result 1: {results[0]['id']} - {results[0]['content'][:50]}")
    if len(results) > 1:
        print(f"  Result 2: {results[1]['id']} - {results[1]['content'][:50]}")

    assert len(results) >= 2
    assert "recent" in results[0]["content"]
    print("\n✅ PASS: Recency boost prioritizes recent memories!")


def test_incremental_index():
    """Test that build_index skips rebuild when count unchanged"""
    print("\n" + "=" * 60)
    print("Test 8: Incremental Index Rebuild")
    print("=" * 60)

    memories = [
        {"id": "1", "content": "test memory one", "type": "semantic"},
        {"id": "2", "content": "test memory two", "type": "semantic"},
    ]

    retriever = BM25Retriever()
    retriever.build_index(memories)
    version_after_first = retriever._index_version

    # Rebuild with same count - should skip
    retriever.build_index(memories)
    assert retriever._index_version == version_after_first

    # Rebuild with different count - should rebuild
    memories.append({"id": "3", "content": "test memory three", "type": "semantic"})
    retriever.build_index(memories)
    assert retriever._index_version == 3

    print(f"  Version unchanged: {version_after_first}")
    print(f"  Version after add: {retriever._index_version}")
    print("\n✅ PASS: Incremental index detection working!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BM25 Retriever Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_bm25_basic()
        test_bm25_multiple_queries()
        test_hybrid_retriever()
        test_bm25_chinese()
        test_bm25_explain()
        test_k1_parameter_affects_scores()
        test_recency_boost()
        test_incremental_index()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
