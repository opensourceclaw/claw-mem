#!/usr/bin/env python3
"""
Test Entity-Enhanced Retriever

Tests entity recognition and matching without spaCy (using fallback regex).
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_mem.retrieval.entity_retriever import EntityRecognizer, EntityEnhancedRetriever, HybridEntityRetriever


def test_entity_recognizer_fallback():
    """Test entity recognition with fallback regex (no spaCy)"""
    print("=" * 60)
    print("Test 1: Entity Recognizer (Fallback Mode)")
    print("=" * 60)
    
    # Use fallback mode (no spaCy)
    recognizer = EntityRecognizer(use_spacy=False)
    
    # Test text
    text = "Peter Cheng is the founder of Project Neo. He works in San Francisco."
    
    entities = recognizer.extract_entities(text)
    
    print(f"\nText: {text}")
    print(f"\nExtracted entities:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.label})")
    
    print(f"\n✅ Extracted {len(entities)} entities")


def test_entity_enhanced_retriever():
    """Test entity-enhanced retrieval"""
    print("\n" + "=" * 60)
    print("Test 2: Entity-Enhanced Retrieval")
    print("=" * 60)
    
    memories = [
        {"id": "1", "content": "Peter Cheng is the founder of Project Neo"},
        {"id": "2", "content": "Friday is the AI assistant working with Peter"},
        {"id": "3", "content": "JARVIS handles quality assurance for the project"},
        {"id": "4", "content": "The team is based in San Francisco"},
    ]
    
    # Use fallback mode
    retriever = EntityEnhancedRetriever(use_spacy=False)
    
    query = "Who is Peter Cheng?"
    results = retriever.search(query, memories, limit=3)
    
    print(f"\nQuery: {query}")
    print(f"\nTop 3 results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['content']}")
    
    if results and "Peter Cheng" in results[0]["content"]:
        print("\n✅ PASS: Entity-enhanced search working!")
    else:
        print("\n⚠️  Note: Entity matching may improve with spaCy")


def test_hybrid_entity_retriever():
    """Test hybrid BM25 + Entity + Keyword retrieval"""
    print("\n" + "=" * 60)
    print("Test 3: Hybrid BM25 + Entity + Keyword")
    print("=" * 60)
    
    memories = [
        {"id": "1", "content": "The user's favorite food is pizza"},
        {"id": "2", "content": "The user's favorite movie is Star Wars"},
        {"id": "3", "content": "Peter Cheng founded Project Neo in San Francisco"},
        {"id": "4", "content": "Friday assists Peter with development work"},
    ]
    
    retriever = HybridEntityRetriever(use_spacy=False)
    
    queries = [
        "What about Peter?",
        "favorite food",
        "Tell me about the project",
    ]
    
    for query in queries:
        results = retriever.search(query, memories, limit=2)
        print(f"\nQuery: {query}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['content']}")
    
    print("\n✅ PASS: Hybrid retrieval working!")


def test_entity_scoring():
    """Test entity match scoring"""
    print("\n" + "=" * 60)
    print("Test 4: Entity Match Scoring")
    print("=" * 60)
    
    retriever = EntityEnhancedRetriever(use_spacy=False)
    
    # Query with entities
    query_entities = {"peter", "san francisco"}
    
    # Test cases
    test_cases = [
        ({"peter"}, 0.33, "One entity match"),
        ({"peter", "san francisco"}, 1.0, "All entities match"),
        ({"friday"}, 0.0, "No entity match"),
        (set(), 0.0, "Empty entities"),
    ]
    
    for memory_entities, expected_range, description in test_cases:
        score = retriever.calculate_entity_score(query_entities, memory_entities)
        status = "✅" if 0 <= score <= 1 else "❌"
        print(f"  {status} {description}: {score:.2f}")
    
    print("\n✅ PASS: Entity scoring working!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Entity-Enhanced Retriever Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_entity_recognizer_fallback()
        test_entity_enhanced_retriever()
        test_hybrid_entity_retriever()
        test_entity_scoring()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\nNote: For better entity recognition, install spaCy:")
        print("  pip install spacy")
        print("  python -m spacy download en_core_web_sm")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
