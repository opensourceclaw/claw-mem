#!/usr/bin/env python3
"""
Simple CLI for claw-mem (for Claude Code plugin testing)
"""
import sys
import os
import json

# Set silent mode
os.environ['CLAW_MEM_SILENT'] = '1'

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claw_mem.memory_manager import MemoryManager

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_cli.py <command> [args]")
        print("Commands: check, store, recall, stats")
        sys.exit(1)
    
    command = sys.argv[1]
    workspace = os.path.expanduser("~/.claude-mem")
    
    try:
        manager = MemoryManager(workspace=workspace)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    
    if command == "check":
        print(json.dumps({"installed": True, "version": "2.0.0"}))
    
    elif command == "store":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Usage: store <content> <memory_type>"}))
            sys.exit(1)
        content = sys.argv[2]
        memory_type = sys.argv[3]  # episodic, semantic, procedural
        
        success = manager.store(content, memory_type=memory_type)
        print(json.dumps({"id": "generated", "success": success}))
    
    elif command == "recall":
        top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        query = sys.argv[3] if len(sys.argv) > 3 else ""
        
        # Use search instead of recall
        results = manager.search(query if query else "all", limit=top_k)
        result = [
            {
                "id": m.get("id", ""),
                "content": m.get("content", ""),
                "layer": m.get("type", "semantic"),
                "timestamp": m.get("timestamp", ""),
                "relevance": m.get("score", 0)
            }
            for m in results
        ]
        print(json.dumps(result))
    
    elif command == "stats":
        stats = manager.get_stats()
        print(json.dumps(stats))
    
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))

if __name__ == "__main__":
    main()
