#!/usr/bin/env python3
"""Store memory in claw-mem"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Store in claw-mem")
    parser.add_argument("text", help="Memory text")
    parser.add_argument("--category", "-c", default="general", help="Memory category")
    parser.add_argument("--layer", choices=["episodic", "semantic", "procedural"], default="semantic", help="Memory layer")
    parser.add_argument("--workspace", "-w", default="~/.openclaw/workspace", help="Workspace path")
    args = parser.parse_args()
    
    try:
        from claw_mem import MemoryManager
    except ImportError:
        print("❌ claw-mem not installed. Run: pip install claw-mem")
        sys.exit(1)
    
    manager = MemoryManager(workspace=args.workspace)
    manager.store(args.text, layer=args.layer, metadata={"category": args.category})
    print(f"✅ Stored in {args.layer} layer: {args.text[:50]}...")

if __name__ == "__main__":
    main()
