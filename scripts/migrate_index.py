#!/usr/bin/env python3
"""Migrate claw-mem pickle+gzip index to JSON format (v5.0.0).

One-time script: reads old pickle+gzip index files and exports
them as JSON-compatible format for the TypeScript rewrite.

Usage:
    python3 scripts/migrate_index.py
"""

import gzip
import json
import os
import pickle
import sys
import time

INDEX_DIR = os.path.expanduser("~/.claw-mem/index")


def migrate():
    if not os.path.isdir(INDEX_DIR):
        print("No index directory found. Nothing to migrate.")
        return

    old_files = [
        f for f in os.listdir(INDEX_DIR)
        if f.startswith("index_v") and f.endswith(".pkl.gz")
    ]

    if not old_files:
        print("No old pickle index found. Nothing to migrate.")
        return

    for fname in old_files:
        old_path = os.path.join(INDEX_DIR, fname)
        try:
            with gzip.open(old_path, "rb") as f:
                ngram_index = pickle.load(f)  # Dict[str, Set[str]]
                bm25 = pickle.load(f)          # BM25 object

            data = {
                "version": "5.0.0",
                "ngram_index": {k: list(v) for k, v in ngram_index.items()},
                "bm25": {
                    "doc_freq": getattr(bm25, "doc_freq", 0),
                    "doc_count": getattr(bm25, "doc_count", 0),
                    "avg_doc_len": getattr(bm25, "avg_doc_len", 0),
                },
                "timestamp": time.time(),
            }

            new_path = old_path.replace(".pkl.gz", ".json")
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            # Rename old file to prevent re-migration
            os.rename(old_path, old_path + ".migrated")
            print(f"Migrated: {old_path} -> {new_path}")

        except Exception as e:
            print(f"Failed to migrate {old_path}: {e}", file=sys.stderr)


if __name__ == "__main__":
    migrate()
