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
claw-mem Bridge for OpenClaw Plugin
JSON-RPC interface via stdio

Protocol: JSON-RPC 2.0, one JSON object per line on stdout.
All diagnostic output goes to stderr.
"""

import sys
import json
import os
import time
from typing import Any, Dict, Optional


class SearchCache:
    """Simple LRU cache with TTL for search results."""

    def __init__(self, max_size: int = 64, ttl_sec: float = 30.0):
        self._cache: Dict[str, tuple[float, Any]] = {}  # key -> (expiry, value)
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
            # Evict oldest entry
            oldest = min(self._cache.items(), key=lambda kv: kv[1][0])
            del self._cache[oldest[0]]
        key = self._make_key(query, limit, memory_type)
        self._cache[key] = (time.monotonic() + self._ttl, value)

    def invalidate(self):
        self._cache.clear()


class ClawMemBridge:
    """JSON-RPC Bridge for claw-mem"""

    def __init__(self):
        self.request_count = 0
        self.total_latency = 0.0
        self.memory_manager = None
        self._search_cache = SearchCache(max_size=64, ttl_sec=30.0)
        self._initialize()

    def _initialize(self):
        """Initialize MemoryManager (suppress stdout during import)."""
        import io
        _saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        init_ok = False
        try:
            try:
                from claw_mem import MemoryManager
                workspace = os.environ.get('OPENCLAW_WORKSPACE', os.getcwd())
                self.memory_manager = MemoryManager(workspace=workspace)
                init_ok = True
            except Exception as e:
                self._respond(0, {"status": "error", "error": str(e)}, -32000)
                raise
        finally:
            sys.stdout = _saved_stdout

        if init_ok:
            self._respond(0, {"status": "ok", "message": "initialized", "version": "2.6.0"})

    def _respond(self, request_id: Any, result: Any, error_code: Optional[int] = None):
        """Send a JSON-RPC response directly to the real stdout (one line)."""
        response: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
        }

        if error_code is not None:
            response["error"] = {
                "code": error_code,
                "message": result if isinstance(result, str) else str(result)
            }
        else:
            response["result"] = result

        # Write directly to the real stdout fd, bypassing any wrappers
        line = json.dumps(response, ensure_ascii=False) + "\n"
        sys.__stdout__.write(line)
        sys.__stdout__.flush()

    def _log(self, msg: str):
        """Write diagnostic message to stderr."""
        print(f"[claw-mem bridge] {msg}", file=sys.stderr, flush=True)

    def _handle_request(self, request: Dict) -> Any:
        """Handle JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        if not method:
            return self._respond(req_id, "Method not found", -32601)

        # Route to handler
        handlers = {
            "search": self._handle_search,
            "store": self._handle_store,
            "get": self._handle_get,
            "delete": self._handle_delete,
            "ping": self._handle_ping,
            "status": self._handle_status,
            # Plugin Slots handlers (v2.5.0)
            "build_context": self._handle_build_context,
            "start_session": self._handle_start_session,
            "end_session": self._handle_end_session,
            "resolve_flush_plan": self._handle_resolve_flush_plan,
        }

        handler = handlers.get(method)
        if not handler:
            return self._respond(req_id, f"Method '{method}' not found", -32601)

        try:
            result = handler(params)
            return self._respond(req_id, result)
        except Exception as e:
            return self._respond(req_id, str(e), -32000)

    # ---- handlers -------------------------------------------------------

    def _handle_search(self, params: Dict) -> Dict:
        query = params.get("query", "")
        top_k = params.get("topK", params.get("top_k", 10))
        memory_type = params.get("memory_type", "episodic")

        # Check cache first
        cached = self._search_cache.get(query, top_k, memory_type)
        if cached is not None:
            return cached

        results = self.memory_manager.search(
            query=query,
            limit=top_k,
            memory_type=memory_type
        )

        result = {
            "results": [
                {
                    "id": r.get("id", ""),
                    "text": r.get("text", r.get("content", "")),
                    "score": r.get("score", 0),
                    "metadata": r.get("metadata", {})
                }
                for r in results
            ]
        }

        # Cache result
        self._search_cache.set(query, top_k, memory_type, result)
        return result

    def _handle_store(self, params: Dict) -> Dict:
        text = params.get("text", "")
        metadata = params.get("metadata", {})
        memory_type = params.get("memory_type", "episodic")

        # Invalidate cache on write
        self._search_cache.invalidate()

        memory_id = self.memory_manager.store(
            content=text,
            memory_type=memory_type,
            metadata=metadata
        )

        return {"id": memory_id, "status": "stored"}

    def _handle_get(self, params: Dict) -> Dict:
        memory_id = params.get("id", "")
        memory = self.memory_manager.get(memory_id)
        if memory:
            return {
                "id": memory.get("id"),
                "text": memory.get("content", ""),
                "metadata": memory.get("metadata", {})
            }
        return {"error": "Memory not found"}

    def _handle_delete(self, params: Dict) -> Dict:
        memory_id = params.get("id", "")
        success = self.memory_manager.delete(memory_id)
        return {"deleted": success}

    def _handle_ping(self, params: Dict) -> Dict:
        return {"pong": True}

    def _handle_status(self, params: Dict) -> Dict:
        return {
            "status": "ok",
            "initialized": self.memory_manager is not None,
            "workspace": os.getcwd()
        }

    def _handle_build_context(self, params: Dict) -> Dict:
        """Build memory context for prompt injection (Plugin Slots promptBuilder)"""
        try:
            top_k = params.get("topK", 10)
            query = params.get("query", "important recent context")

            results = self.memory_manager.search(query=query, limit=top_k)
            if not results:
                return {"context": [], "count": 0}

            from claw_mem.context_injection import format_memory_context
            context_str = format_memory_context(results, max_length=4000)

            return {
                "context": [context_str] if context_str else [],
                "count": len(results)
            }
        except Exception as e:
            return {"context": [], "count": 0, "error": str(e)}

    def _handle_start_session(self, params: Dict) -> Dict:
        """Start a memory session (Plugin Slots runtime)"""
        try:
            session_id = params.get("sessionId", "default")
            self.memory_manager.start_session(session_id)
            return {"status": "started", "sessionId": session_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _handle_end_session(self, params: Dict) -> Dict:
        """End a memory session (Plugin Slots runtime)"""
        try:
            session_id = params.get("sessionId", "default")
            self.memory_manager.end_session()
            return {"status": "ended", "sessionId": session_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _handle_resolve_flush_plan(self, params: Dict) -> Dict:
        """Compute a dynamic compaction (flush) plan based on memory state."""
        from datetime import datetime as dt
        try:
            stats = self.memory_manager.get_stats()
            total_memories = sum(
                stats.get(k, 0) for k in ("episodic", "semantic", "procedural")
                if isinstance(stats.get(k), (int, float))
            )

            # Scale thresholds based on memory volume
            # More memories → more aggressive compaction
            base_soft = 100000
            base_force = 500000
            base_reserve = 20000
            if total_memories > 500:
                base_soft = 80000
                base_force = 400000
                base_reserve = 15000

            ts = dt.now().strftime("%Y%m%d-%H%M%S")
            return {
                "softThresholdTokens": base_soft,
                "forceFlushTranscriptBytes": base_force,
                "reserveTokensFloor": base_reserve,
                "prompt": (
                    "Summarize the conversation transcript below. "
                    "Preserve key decisions, user preferences, domain knowledge, "
                    "and action items. Remove redundancy."
                ),
                "systemPrompt": (
                    "You are a conversation summarizer for an AI memory system. "
                    "Extract essential information. Be concise."
                ),
                "relativePath": f"compaction/flush-{ts}.md",
                "totalMemories": total_memories,
                "stats": stats,
            }
        except Exception as e:
            return {"error": str(e)}

    # ---- main loop ------------------------------------------------------

    def run(self):
        """Main loop: read JSON-RPC lines from stdin, respond on stdout."""
        self._log("Starting v2.6.0...")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                self._handle_request(request)
                self.request_count += 1
            except json.JSONDecodeError as e:
                self._respond(None, f"Invalid JSON: {e}", -32700)
            except Exception as e:
                self._respond(None, str(e), -32000)

        self._log(f"Shutting down. Total requests: {self.request_count}")


def main():
    """Entry point"""
    bridge = ClawMemBridge()
    bridge.run()


if __name__ == "__main__":
    main()
