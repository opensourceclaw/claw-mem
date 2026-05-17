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
EngramIndex - O(1) N-Gram hash inverted index (v2.15.0).

Provides sub-millisecond lookup via N-gram hashing with Jaccard similarity
scoring. Complements the existing InMemoryIndex as the primary search path.
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


class EngramHasher:
    """N-Gram → Deterministic hash converter.

    Uses SHA-256 (truncated to 64 bits) for collision-resistant hashing.
    Replaceable with xxHash when the optional dependency is available.
    """

    def __init__(self, ngram_size: int = 3):
        self.ngram_size = ngram_size

    def hash_ngram(self, ngram: str) -> int:
        """Hash a single n-gram to a 64-bit integer."""
        digest = hashlib.sha256(ngram.encode('utf-8')).digest()
        return int.from_bytes(digest[:8], 'big')

    def hash_text(self, text: str, ngram_size: int = None) -> List[int]:
        """Extract all n-grams from text and hash them.

        Args:
            text: Input text.
            ngram_size: Override the instance ngram_size.

        Returns:
            List of hash integers, one per n-gram.
        """
        size = ngram_size if ngram_size is not None else self.ngram_size
        cleaned = self._preprocess(text)
        if len(cleaned) < size:
            return []

        hashes = []
        for i in range(len(cleaned) - size + 1):
            ngram = cleaned[i:i + size]
            hashes.append(self.hash_ngram(ngram))
        return hashes

    def _preprocess(self, text: str) -> str:
        """Clean text for n-gram extraction."""
        if not text:
            return ''
        if re.search(r'[\u4e00-\u9fff]', text):
            # Chinese: keep Chinese chars + alphanumeric
            text = re.sub(r'[^\u4e00-\u9fff\w]', '', text)
            return text.lower()
        # English/other: lowercase, remove punctuation, join words
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return ''.join(text.split())


@dataclass
class EngramEntry:
    """Per-memory index entry."""
    memory_id: str
    ngram_count: int
    ngram_hashes: Set[int] = field(default_factory=set)


class EngramIndex:
    """O(1) N-Gram hash inverted index.

    Structure:
        _inverted: {hash_value → [memory_id, ...]}
        _entries:  {memory_id → EngramEntry}

    Query flow:
        1. Hash query n-grams → [h1, h2, ...]
        2. Collect candidates from inverted index (Counter)
        3. Score with Jaccard + frequency weighting
        4. Return top-k
    """

    def __init__(self, ngram_size: int = 3):
        self._hasher = EngramHasher(ngram_size)
        self._inverted: Dict[int, List[str]] = {}
        self._entries: Dict[str, EngramEntry] = {}

    # ── Indexing ─────────────────────────────────────────────

    def index(self, memory_id: str, content: str) -> None:
        """Index a single memory.

        Args:
            memory_id: Unique memory identifier.
            content: Memory text content.
        """
        hashes = self._hasher.hash_text(content)
        unique_hashes = set(hashes)

        if not unique_hashes:
            return

        # Store entry (idempotent overwrite)
        self._entries[memory_id] = EngramEntry(
            memory_id=memory_id,
            ngram_count=len(hashes),
            ngram_hashes=unique_hashes,
        )

        # Update inverted index
        for h in unique_hashes:
            bucket = self._inverted.setdefault(h, [])
            if memory_id not in bucket:
                bucket.append(memory_id)

    def index_batch(self, items: List[Tuple[str, str]]) -> None:
        """Index multiple memories in batch.

        Args:
            items: [(memory_id, content), ...]
        """
        for memory_id, content in items:
            self.index(memory_id, content)

    # ── Query ─────────────────────────────────────────────────

    def lookup(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """O(1) hash lookup with Jaccard scoring.

        Args:
            query: Search query.
            top_k: Maximum number of results.

        Returns:
            [(memory_id, score), ...] ordered by descending score.
        """
        query_hashes = self._hasher.hash_text(query)
        if not query_hashes:
            return []

        # Step 1: Collect candidates via inverted index
        hit_counter: Counter = Counter()
        for h in query_hashes:
            bucket = self._inverted.get(h)
            if bucket:
                for mid in bucket:
                    hit_counter[mid] += 1

        if not hit_counter:
            return []

        # Step 2: Jaccard similarity scoring
        query_set = set(query_hashes)
        scored: List[Tuple[str, float]] = []

        for mid, hit_count in hit_counter.most_common(min(top_k * 5, len(hit_counter))):
            entry = self._entries.get(mid)
            if entry is None:
                continue

            intersection = len(query_set & entry.ngram_hashes)
            union = len(query_set | entry.ngram_hashes)
            jaccard = intersection / union if union > 0 else 0.0

            freq_score = hit_count / len(query_hashes)
            score = jaccard * 0.7 + freq_score * 0.3
            scored.append((mid, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ── Removal ───────────────────────────────────────────────

    def remove(self, memory_id: str) -> None:
        """Remove a memory from the index.

        Args:
            memory_id: Memory ID to remove.
        """
        entry = self._entries.pop(memory_id, None)
        if entry is None:
            return

        for h in entry.ngram_hashes:
            bucket = self._inverted.get(h)
            if bucket:
                if memory_id in bucket:
                    bucket.remove(memory_id)
                if not bucket:
                    del self._inverted[h]

    # ── Stats ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "memory_count": len(self._entries),
            "hash_count": len(self._inverted),
            "total_ngrams": sum(
                e.ngram_count for e in self._entries.values()
            ),
            "memory_estimate_bytes": self._estimate_memory(),
        }

    def _estimate_memory(self) -> int:
        """Rough memory estimate in bytes."""
        # Each hash bucket: ~200 bytes overhead
        inverted_cost = len(self._inverted) * 200
        # Each entry: ~500 bytes
        entry_cost = len(self._entries) * 500
        return inverted_cost + entry_cost
