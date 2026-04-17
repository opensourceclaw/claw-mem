#!/usr/bin/env python3
"""Start claw-mem JSON-RPC bridge"""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Start claw-mem bridge")
    parser.add_argument("--workspace", "-w", default="~/.openclaw/workspace", help="Workspace path")
    args = parser.parse_args()
    
    try:
        from claw_mem.bridge import run_bridge
    except ImportError:
        print("❌ claw-mem not installed. Run: pip install claw-mem")
        return
    
    print(f"🧠 Starting claw-mem bridge for {args.workspace}")
    run_bridge(workspace=args.workspace)

if __name__ == "__main__":
    main()
