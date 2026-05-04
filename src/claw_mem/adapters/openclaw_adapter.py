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
OpenClawAdapter: Generic adapter that wraps MemoryManager with version-strategy delegation.

Responsibilities:
- Search caching (SearchCache)
- Common CRUD operations (search, store, get, delete)
- Session management (start/end)
- Delegates version-specific logic to BaseAdapter strategy
"""

import os
import time
from typing import Any, Dict, List, Optional

from .base import BaseAdapter


class SearchCache:
    """Simple LRU cache with TTL for search results."""

    def __init__(self, max_size: int = 64, ttl_sec: float = 30.0):
        self._cache: Dict[str, tuple] = {}  # key -> (expiry, value)
        self._max_size = max_size
        self._ttl = ttl_sec

    def _make_key(self, query: str, limit: int, memory_type: str) -> str:
        return f"{query}|{limit}|{memory_type}"

    def get(self, query: str, limit: int, memory_type: str) -> Optional[Any]:
        key = self._make_key(query, limit, memory_type)
        entry = self._cache.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.monotonic() > expiry:
            del self._cache[key]
            return None
        return value

    def set(self, query: str, limit: int, memory_type: str, value: Any):
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.items(), key=lambda kv: kv[1][0])
            del self._cache[oldest[0]]
        key = self._make_key(query, limit, memory_type)
        self._cache[key] = (time.monotonic() + self._ttl, value)

    def invalidate(self):
        self._cache.clear()


class OpenClawAdapter:
    """Generic adapter for claw-mem MemoryManager operations."""

    def __init__(self, memory_manager: Any, strategy: BaseAdapter):
        self.memory_manager = memory_manager
        self._strategy = strategy
        self._search_cache = SearchCache(max_size=64, ttl_sec=30.0)

    @property
    def version(self) -> str:
        """Return the adapter's targeted OpenClaw version."""
        return self._strategy.get_version()

    @property
    def strategy(self) -> BaseAdapter:
        """Return the underlying strategy instance."""
        return self._strategy

    def get_initialize_response(self) -> Dict:
        """Build the startup response for the bridge."""
        return self._strategy.get_initialize_response()

    # ---- CRUD operations -----------------------------------------------

    def search(self, params: Dict) -> List[Dict]:
        """Search memories with caching."""
        query = params.get("query", "")
        top_k = params.get("topK", params.get("top_k", 10))
        memory_type = params.get("memory_type", "episodic")

        cached = self._search_cache.get(query, top_k, memory_type)
        if cached is not None:
            return cached

        results = self.memory_manager.search(
            query=query,
            limit=top_k,
            memory_type=memory_type,
        )

        formatted = [self._strategy.format_search_result(r) for r in results]
        self._search_cache.set(query, top_k, memory_type, formatted)
        return formatted

    def store(self, params: Dict) -> Dict:
        """Store a memory and invalidate search cache."""
        text = params.get("text", "")
        metadata = params.get("metadata", {})
        memory_type = params.get("memory_type", "episodic")

        self._search_cache.invalidate()

        memory_id = self.memory_manager.store(
            content=text,
            memory_type=memory_type,
            metadata=metadata,
        )

        return {"id": memory_id, "status": "stored"}

    def get(self, params: Dict) -> Dict:
        """Retrieve a single memory by ID."""
        memory_id = params.get("id", "")
        memory = self.memory_manager.get(memory_id)
        if memory:
            return {
                "id": memory.get("id"),
                "text": memory.get("content", ""),
                "metadata": memory.get("metadata", {}),
            }
        return {"error": "Memory not found"}

    def delete(self, params: Dict) -> Dict:
        """Delete a memory by ID."""
        memory_id = params.get("id", "")
        success = self.memory_manager.delete(memory_id)
        return {"deleted": success}

    def ping(self, params: Dict = None) -> Dict:
        """Health check ping."""
        return {"pong": True}

    def status(self, params: Dict = None) -> Dict:
        """Return bridge status."""
        return {
            "status": "ok",
            "initialized": self.memory_manager is not None,
            "workspace": os.getcwd(),
        }

    # ---- Plugin Slots handlers -----------------------------------------

    def build_context(self, params: Dict) -> Dict:
        """Build memory context (delegates to strategy)."""
        return self._strategy.build_context(self.memory_manager, params)

    def resolve_flush_plan(self, params: Dict) -> Dict:
        """Compute flush plan (delegates to strategy)."""
        return self._strategy.resolve_flush_plan(self.memory_manager, params)

    def start_session(self, params: Dict) -> Dict:
        """Start a memory session."""
        try:
            session_id = params.get("sessionId", "default")
            self.memory_manager.start_session(session_id)
            return {"status": "started", "sessionId": session_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def end_session(self, params: Dict) -> Dict:
        """End a memory session."""
        try:
            session_id = params.get("sessionId", "default")
            self.memory_manager.end_session()
            return {"status": "ended", "sessionId": session_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def sessions(self, params: Dict = None) -> Dict:
        """List active sessions."""
        try:
            sessions = getattr(self.memory_manager, "sessions", [])
            return {"sessions": list(sessions) if sessions else []}
        except Exception as e:
            return {"error": str(e)}
