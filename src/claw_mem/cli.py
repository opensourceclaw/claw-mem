#!/usr/bin/env python3
# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
claw-mem CLI - Command Line Interface for claw-mem

AI Harness Engineering Memory System for OpenClaw
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigDetector
from .retrieval.three_tier import ThreeTierRetriever


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="claw-mem",
        description="AI Harness Engineering Memory System for OpenClaw",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    parser.add_argument(
        "--workspace",
        type=str,
        default=None,
        help="OpenClaw workspace path (default: auto-detect)",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show memory statistics")
    stats_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search memories (three-tier retrieval)")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    search_parser.add_argument(
        "--layers",
        type=str,
        default="l1,l2,l3",
        help="Layers to search: l1,l2,l3 (default: all)",
    )
    search_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    
    # backup command
    backup_parser = subparsers.add_parser("backup", help="Backup memories")
    backup_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: auto-generated)",
    )
    
    # restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("file", type=str, help="Backup file to restore")
    
    # parse arguments
    args = parser.parse_args()
    
    # handle commands
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    elif args.command == "stats":
        cmd_stats(args)
    
    elif args.command == "search":
        cmd_search(args)
    
    elif args.command == "backup":
        cmd_backup(args)
    
    elif args.command == "restore":
        cmd_restore(args)
    
    else:
        parser.print_help()
        sys.exit(1)


def cmd_stats(args):
    """Show memory statistics"""
    from .memory_manager import MemoryManager

    # Detect workspace
    try:
        workspace = ConfigDetector.detect_workspace()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Initialize memory manager
    mm = MemoryManager(workspace=workspace, auto_detect=False)

    stats = mm.get_stats()

    if args.json:
        import json
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print("claw-mem Memory Statistics")
        print("=" * 40)
        print(f"Workspace: {stats['workspace']}")
        print(f"Session: {stats['session_id'] or 'None'}")
        print(f"Working memory count: {stats['working_memory_count']}")
        print(f"L1 cache size: {stats['working_cache_size']}")
        print(f"Index built: {stats['index_built']}")
        print(f"Episodic memories: {stats['episodic_count']}")
        print(f"Semantic memories: {stats['semantic_count']}")
        print(f"Procedural memories: {stats['procedural_count']}")
        print("=" * 40)
        print(f"Total memories: {stats['episodic_count'] + stats['semantic_count'] + stats['procedural_count']}")


def cmd_search(args):
    """Search memories using three-tier retrieval"""
    # Detect workspace
    try:
        workspace = ConfigDetector.detect_workspace()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Parse layers
    layers = [l.strip() for l in args.layers.split(",")]

    # Initialize retriever
    retriever = ThreeTierRetriever(Path(workspace))

    # Search
    results = retriever.search(
        query=args.query,
        layers=layers,
        limit=args.limit,
    )

    if args.json:
        import json
        output = {
            "query": args.query,
            "layers": layers,
            "count": len(results),
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"Search results for: {args.query}")
        print(f"Layers searched: {', '.join(layers)}")
        print(f"Found {len(results)} results")
        print("=" * 60)

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] [{result.layer.value.upper()}] (score: {result.score:.3f})")
            print(f"    {result.content[:200]}{'...' if len(result.content) > 200 else ''}")
            if result.source != "working_memory":
                print(f"    Source: {Path(result.source).name}")
            if result.tags:
                print(f"    Tags: {', '.join(result.tags)}")


def cmd_backup(args):
    """Backup memories"""
    output = args.output or "claw-mem-backup.json"
    print(f"Backing up memories to: {output}")
    print("=" * 40)
    print("Note: Full backup implementation coming in v0.8.0")
    print("=" * 40)


def cmd_restore(args):
    """Restore from backup"""
    print(f"Restoring from: {args.file}")
    print("=" * 40)
    print("Note: Full restore implementation coming in v0.8.0")
    print("=" * 40)


if __name__ == "__main__":
    main()
