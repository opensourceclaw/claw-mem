#!/usr/bin/env python3
"""
Quick Benchmark Test - Test first 50 samples
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from claw_mem import MemoryManager
from datetime import datetime

def quick_test():
    """Quick test with 50 samples"""
    print("=" * 80)
    print("Quick Benchmark Test (50 samples)")
    print("=" * 80)
    
    # Initialize memory manager with smart mode
    mm = MemoryManager(workspace="workspace_test")
    mm.search_mode = "smart"  # Use our new smart retriever
    
    # Load test data
    data_file = Path("data/longmemeval/test_data.json")
    facts_file = Path("data/longmemeval/facts.json")
    
    with open(data_file, 'r') as f:
        test_data = json.load(f)
    
    with open(facts_file, 'r') as f:
        facts = json.load(f)
    
    # Preload facts
    print(f"\nPreloading {len(facts)} facts...")
    for fact in facts:
        mm.store(
            content=fact["fact"],
            memory_type="semantic",
            metadata={"test_id": fact["id"], "category": fact.get("category", "")}
        )
    print(f"✓ Preloaded {len(facts)} facts")
    
    # Test first 50 samples
    print(f"\nTesting first 50 samples...")
    test_subset = test_data[:50]
    
    correct = 0
    total = len(test_subset)
    
    for i, test_case in enumerate(test_subset):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{total}")
        
        # Search with smart mode
        results = mm.search(
            query=test_case["question"],
            limit=5
        )
        
        # Check if answer is in results
        answer = test_case["ground_truth"]
        if results:
            # Check if answer appears in any result
            found = any(answer.lower() in r.get("content", "").lower() for r in results)
            if found:
                correct += 1
    
    accuracy = correct / total if total > 0 else 0
    
    print(f"\n{'=' * 80}")
    print(f"Quick Test Results")
    print(f"{'=' * 80}")
    print(f"Total: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"Search Mode: smart (BM25 + Entity + Time + Type + Keyword)")
    print(f"{'=' * 80}\n")
    
    return accuracy

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)
    quick_test()
