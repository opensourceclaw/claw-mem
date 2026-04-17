#!/usr/bin/env python3
"""Search claw-mem memory store"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Search claw-mem")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max results")
    parser.add_argument("--mode", choices=["keyword", "bm25", "hybrid", "entity", "heuristic", "smart", "enhanced_smart"], default="enhanced_smart", help="Search mode")
    parser.add_argument("--workspace", "-w", default="~/.openclaw/workspace", help="Workspace path")
    args = parser.parse_args()
    
    try:
        from claw_mem import MemoryManager
    except ImportError:
        print("❌ claw-mem not installed. Run: pip install claw-mem")
        sys.exit(1)
    
    manager = MemoryManager(workspace=args.workspace)
    
    # Set search mode
    import os
    os.environ['CLAW_MEM_SEARCH_MODE'] = args.mode
    
    results = manager.search(args.query, top_k=args.limit)
    
    if not results:
        print("No results found")
        return
    
    for i, r in enumerate(results, 1):
        layer = r.get('layer', 'unknown')
        content = r.get('content', '')[:100]
        score = r.get('score', 0)
        print(f"{i}. [{layer}] {content}...")
        if score:
            print(f"   Score: {score:.3f}")

if __name__ == "__main__":
    main()
