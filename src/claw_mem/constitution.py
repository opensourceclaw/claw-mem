"""
ConstitutionStore — Three-layer persistent identity store for claw-mem.

Contrary to regular memory (episodic/semantic/procedural) which is subject
to decay and compression, constitution data is:

  • NEVER decayed or compressed
  • ALWAYS injected at session start (Stage 0 of start_session)
  • Storage is file-system based (model-agnostic, survives model swaps)
  • Writes require explicit governance (Layer 0 = human, Layer 1 = validated,
    Layer 2 = RPC)

Three layers mirror the Memory-as-Ontology philosophy (but simplified):

  L0 — Immutable Constitution    (AGENTS.md, IDENTITY.md, MEMORY.md, TOOLS.md)
  L1 — Persistent Rules          (auto-detected via classifier, pending approval)
  L2 — Session Anchors           (stored via RPC by operator)

Layer hierarchy:
  L0 > L1 > L2 — when conflict occurs, higher layer wins.
  All layers are immune to decay and compression.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── File paths that serve as L0 constitution sources ──────────────
L0_FILE_PATTERNS: list[str] = [
    "AGENTS.md",
    "IDENTITY.md",
    "MEMORY.md",
    "TOOLS.md",
    "USER.md",
]

L1_STORAGE_DIR = ".claw-mem/constitution"


# ── Entry types ────────────────────────────────────────────────────

class ConstitutionEntry:
    """A single constitution entry with layer provenance."""

    __slots__ = ("id", "layer", "source", "content", "created_at", "tags")

    def __init__(
        self,
        entry_id: str,
        layer: int,  # 0 | 1 | 2
        source: str,
        content: str,
        created_at: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ):
        self.id = entry_id
        self.layer = layer
        self.source = source
        self.content = content
        self.created_at = created_at or datetime.now().isoformat()
        self.tags = tags or []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "layer": self.layer,
            "source": self.source,
            "content": self.content,
            "created_at": self.created_at,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConstitutionEntry":
        return cls(
            entry_id=data["id"],
            layer=data["layer"],
            source=data["source"],
            content=data["content"],
            created_at=data.get("created_at"),
            tags=data.get("tags", []),
        )


# ── ConstitutionStore ──────────────────────────────────────────────

class ConstitutionStore:
    """Manages three-layer constitution data for claw-mem.

    Usage::

        store = ConstitutionStore(workspace="/path/to/workspace")
        entries = store.assemble()       # returns all entries L0+L1+L2
        store.scan_and_suggest("...")    # analyzes content for L1 candidates
        store.promote("entry-id")       # promotes L1 → L2
        store.store_via_rpc(...)        # direct L2 write via bridge
    """

    def __init__(self, workspace: str) -> None:
        self._workspace = Path(workspace).expanduser().resolve()
        self._l1_dir = self._workspace / L1_STORAGE_DIR
        self._l1_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._entries: list[ConstitutionEntry] = []
        self._dirty = False

    # ── public API ──────────────────────────────────────────────────

    def assemble(self) -> list[dict]:
        """Gather all constitution entries (L0 + L1 + L2) for session injection.

        Returns a list of dicts sorted by layer (L0 first).
        """
        self._load_if_needed()
        # Stable sort: L0 → L1 → L2
        sorted_entries = sorted(self._entries, key=lambda e: (e.layer, e.id))
        return [e.to_dict() for e in sorted_entries]

    def assemble_text(self, separator: str = "\n---\n") -> str:
        """Return constitution as a single text block for prompt injection."""
        entries = self.assemble()
        if not entries:
            return ""
        parts: list[str] = []
        for e in entries:
            tag_info = f" [{', '.join(e['tags'])}]" if e["tags"] else ""
            parts.append(f"[L{e['layer']}]{tag_info} {e['content']}")
        return separator.join(parts)

    def scan_and_suggest(self, conversations: list[dict]) -> list[dict]:
        """Scan conversation history for content that should be promoted to L1.

        Uses simple heuristic rules:
          - Technical stack decisions (TypeScript, Python, etc.)
          - Protocol agreements (use file system, use RPC, etc.)
          - Role definitions (Friday is strategist, Jarvis is executor)

        Returns a list of suggestion dicts with keys:
          content, source, confidence, reason
        """
        suggestions: list[dict] = []
        seen = {e.content for e in self._entries}

        patterns: list[tuple[str, str, float]] = [
            # (source_tag, content_substring_match, confidence)
            ("tech_stack", r"use\s+(TypeScript|Python|Rust|Go|React|Vue)", 0.95),
            ("tech_stack", r"project\s+(uses|runs on|is built with)\s+\w+", 0.85),
            ("protocol", r"communication\s+(protocol|method|via)\s+\w+", 0.90),
            ("protocol", r"comm\s+(via|through|using)\s+\w+", 0.85),
            ("role", r"(\w+)\s+(is responsible for|handles|owns)\s+\w+", 0.90),
            ("role", r"(\w+)\s+(role|responsibility|job)\s+is\s+", 0.90),
            ("rule", r"always\s+use\s+\w+", 0.80),
            ("rule", r"never\s+use\s+\w+", 0.80),
            ("rule", r"must\s+always\s+\w+", 0.85),
            ("rule", r"do not\s+use\s+\w+", 0.80),
            ("decision", r"let'?s?\s+(use|go with|stick with)\s+\w+", 0.85),
            ("decision", r"we'?ll?\s+(use|go with)\s+\w+", 0.85),
            ("decision", r"decided\s+to\s+use\s+\w+", 0.90),
        ]

        for msg in conversations:
            content = msg.get("content", "")
            if not content or not isinstance(content, str):
                continue
            content_lower = content.lower()

            for tag, pattern, confidence in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if not match:
                    continue
                # Extract a concise summary
                matched_text = match.group(0)
                # Skip if this text (or a superset) is already in constitution
                if any(matched_text in s or s in matched_text for s in seen):
                    continue

                suggestions.append({
                    "content": matched_text,
                    "source": tag,
                    "confidence": confidence,
                    "reason": f"Matched pattern '{pattern}' in session content",
                    "source_message": content[:200],
                })

        # Deduplicate by content (substring aware)
        seen_texts: set[str] = set()
        deduped: list[dict] = []
        for s in suggestions:
            # Skip if this content is already a substring of a seen suggestion
            if any(s["content"] in t or t in s["content"] for t in seen_texts):
                continue
            # Skip if already in constitution
            if s["content"] in seen:
                continue
            seen_texts.add(s["content"])
            deduped.append(s)

        return deduped[:10]  # max 10 suggestions per scan

    def promote_to_l1(self, content: str, source: str = "auto_detect") -> Optional[str]:
        """Promote content to L1 (persistent rule, pending approval).

        Returns the entry ID if created, None if already exists.
        """
        # Check for duplicates
        for e in self._entries:
            if e.content == content:
                return None

        import uuid
        entry_id = f"l1_{uuid.uuid4().hex[:8]}"

        entry = ConstitutionEntry(
            entry_id=entry_id,
            layer=1,
            source=source,
            content=content,
        )
        self._entries.append(entry)
        self._persist_l1(entry)
        self._dirty = True
        return entry_id

    def promote_to_l2(self, content: str, source: str = "rpc", tags: Optional[list[str]] = None) -> Optional[str]:
        """Directly store as L2 (operator-validated rule).

        Returns the entry ID if created, None if already exists.
        """
        for e in self._entries:
            if e.content == content:
                return None

        import uuid
        entry_id = f"l2_{uuid.uuid4().hex[:8]}"

        entry = ConstitutionEntry(
            entry_id=entry_id,
            layer=2,
            source=source,
            content=content,
            tags=tags,
        )
        self._entries.append(entry)
        self._persist_l1(entry)  # L2 also stored in same directory
        self._dirty = True
        return entry_id

    def delete(self, entry_id: str) -> bool:
        """Delete a constitution entry by ID. L0 entries cannot be deleted via API."""
        before = len(self._entries)
        removed = [e for e in self._entries if e.id == entry_id]
        if not removed:
            return False
        if removed[0].layer == 0:
            logger.warning("Cannot delete L0 entry %s via API — modify file directly", entry_id)
            return False
        self._entries = [e for e in self._entries if e.id != entry_id]
        self._remove_l1_file(entry_id)
        self._dirty = True
        return True

    def get_all(self) -> list[dict]:
        """Return all entries as dicts."""
        self._load_if_needed()
        return [e.to_dict() for e in self._entries]

    def get_stats(self) -> dict:
        """Return statistics about constitution store."""
        self._load_if_needed()
        counts = {0: 0, 1: 0, 2: 0}
        for e in self._entries:
            counts[e.layer] = counts.get(e.layer, 0) + 1
        return {
            "total_entries": len(self._entries),
            "by_layer": counts,
            "sources": list({e.source for e in self._entries}),
        }

    # ── internal: loading ──────────────────────────────────────────

    def _load_if_needed(self) -> None:
        """Load entries if not yet loaded or if workspace files changed."""
        if self._entries and not self._dirty:
            return
        self._entries = []
        self._load_l0()
        self._load_l1_from_disk()
        self._dirty = False

    def _load_l0(self) -> None:
        """Load L0 entries from workspace file system patterns."""
        for pattern in L0_FILE_PATTERNS:
            file_path = self._workspace / pattern
            if not file_path.exists():
                continue
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                # Extract meaningful lines (skip markdown headers, blank lines)
                lines = [
                    line.strip()
                    for line in content.splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
                for line in lines:
                    if len(line) > 10 and not line.startswith("```"):
                        self._entries.append(ConstitutionEntry(
                            entry_id=f"l0_{file_path.stem}_{len(self._entries)}",
                            layer=0,
                            source=str(file_path.relative_to(self._workspace)),
                            content=line[:500],
                        ))
            except (OSError, UnicodeDecodeError) as exc:
                logger.warning("Failed to read L0 source %s: %s", file_path, exc)

    def _load_l1_from_disk(self) -> None:
        """Load L1/L2 entries from on-disk JSONL storage."""
        if not self._l1_dir.exists():
            return
        for fpath in sorted(self._l1_dir.glob("*.json")):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                entry = ConstitutionEntry.from_dict(data)
                self._entries.append(entry)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load constitution entry %s: %s", fpath, exc)

    # ── internal: persistence ──────────────────────────────────────

    def _persist_l1(self, entry: ConstitutionEntry) -> None:
        """Persist a single L1/L2 entry to disk."""
        if entry.layer == 0:
            return  # L0 entries live in their original files
        path = self._l1_dir / f"{entry.id}.json"
        try:
            path.write_text(
                json.dumps(entry.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("Failed to persist constitution entry %s: %s", entry.id, exc)

    def _remove_l1_file(self, entry_id: str) -> None:
        path = self._l1_dir / f"{entry_id}.json"
        if path.exists():
            path.unlink()
