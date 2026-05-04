#!/usr/bin/env python3
"""
claw-mem Bridge - stdio JSON-RPC Server for OpenClaw Plugin

Purpose:
- Receive JSON-RPC requests from TypeScript Plugin via stdin
- Route to claw-mem Python Core
- Return responses via stdout

Protocol: JSON-RPC 2.0

Architecture:
    OpenClaw Plugin (TypeScript)
        ↓ spawn + stdio JSON-RPC
    claw-mem Bridge (Python)
        ↓ Python Function Call
    claw-mem Core (MemoryManager, ThreeTierRetriever)
"""

import sys
import json
import asyncio
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Add claw-mem to path (bridge.py is in root/claw_mem/, MemoryManager is in root/src/claw_mem/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claw_mem import MemoryManager
from claw_mem.adapters import AdapterRegistry


class ClawMemBridge:
    """JSON-RPC Bridge for claw-mem"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.manager: Optional[MemoryManager] = None
        self._adapter = None
        self.running = True
        self.request_count = 0
        self.total_latency = 0.0

        # Register handlers
        self.handlers = {
            "initialize": self._initialize,
            "shutdown": self._shutdown,
            "search": self._search,
            "store": self._store,
            "get": self._get,
            "delete": self._delete,
            "stats": self._stats,
            # Plugin Slots handlers
            "build_context": self._build_context,
            "start_session": self._start_session,
            "end_session": self._end_session,
            "resolve_flush_plan": self._resolve_flush_plan,
        }

    async def _initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MemoryManager and adapter with config"""
        start = time.perf_counter()

        try:
            workspace = params.get("workspace_dir") or params.get("workspace") or self.config.get("workspace")

            self.manager = MemoryManager(workspace=workspace)
            self._adapter = AdapterRegistry.create_adapter(self.manager)

            latency = (time.perf_counter() - start) * 1000

            return {
                "status": "initialized",
                "version": self._adapter.version,
                "workspace": workspace,
                "latency_ms": round(latency, 3)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown the bridge"""
        start = time.perf_counter()

        try:
            self.manager = None
            self._adapter = None
            self.running = False
            latency = (time.perf_counter() - start) * 1000

            return {
                "status": "shutdown",
                "latency_ms": round(latency, 3)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories"""
        start = time.perf_counter()

        try:
            query = params.get("query", "")
            limit = params.get("limit", 10)
            memory_type = params.get("memory_type", "episodic")

            # Use adapter with params in adapter format
            results = self._adapter.search({
                "query": query,
                "topK": limit,
                "memory_type": memory_type,
            })

            latency = (time.perf_counter() - start) * 1000

            return {
                "memories": results,
                "query": query,
                "count": len(results),
                "latency_ms": round(latency, 3)
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store a memory"""
        start = time.perf_counter()

        try:
            text = params.get("text", "")
            metadata = params.get("metadata", {})
            memory_type = params.get("memory_type", "episodic")

            result = self._adapter.store({
                "text": text,
                "metadata": metadata,
                "memory_type": memory_type,
            })

            latency = (time.perf_counter() - start) * 1000

            return {
                "id": result["id"],
                "memory_type": memory_type,
                "latency_ms": round(latency, 3)
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific memory"""
        start = time.perf_counter()
        latency = (time.perf_counter() - start) * 1000

        if not self._adapter:
            return {
                "error": "Adapter not initialized",
                "latency_ms": round(latency, 3)
            }

        try:
            result = self._adapter.get(params)
            result["latency_ms"] = round(latency, 3)
            return result
        except Exception as e:
            return {
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a memory"""
        start = time.perf_counter()
        latency = (time.perf_counter() - start) * 1000

        if not self._adapter:
            return {
                "error": "Adapter not initialized",
                "latency_ms": round(latency, 3)
            }

        try:
            result = self._adapter.delete(params)
            result["latency_ms"] = round(latency, 3)
            return result
        except Exception as e:
            return {
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get bridge statistics"""
        start = time.perf_counter()

        try:
            avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0

            latency = (time.perf_counter() - start) * 1000

            return {
                "request_count": self.request_count,
                "total_latency_ms": round(self.total_latency, 3),
                "avg_latency_ms": round(avg_latency, 3),
                "latency_ms": round(latency, 3)
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _build_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build memory context for prompt injection"""
        start = time.perf_counter()

        try:
            result = self._adapter.build_context(params)

            latency = (time.perf_counter() - start) * 1000
            result["latency_ms"] = round(latency, 3)
            return result
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _start_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a memory session"""
        start = time.perf_counter()

        try:
            result = self._adapter.start_session(params)
            stats = self.manager.get_stats()

            latency = (time.perf_counter() - start) * 1000

            return {
                "status": result.get("status", "started"),
                "sessionId": result.get("sessionId", "default"),
                "latency_ms": round(latency, 3),
                "stats": stats
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "status": "error",
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _end_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """End a memory session"""
        start = time.perf_counter()

        try:
            result = self._adapter.end_session(params)
            stats = self.manager.get_stats()

            latency = (time.perf_counter() - start) * 1000

            return {
                "status": result.get("status", "ended"),
                "sessionId": result.get("sessionId", "default"),
                "latency_ms": round(latency, 3),
                "stats": stats
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "status": "error",
                "error": str(e),
                "latency_ms": round(latency, 3)
            }

    async def _resolve_flush_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute dynamic compaction plan based on memory state"""
        start = time.perf_counter()

        try:
            result = self._adapter.resolve_flush_plan(params)
            latency = (time.perf_counter() - start) * 1000
            result["latency_ms"] = round(latency, 3)
            return result
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {"error": str(e), "latency_ms": round(latency, 3)}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        start = time.perf_counter()

        handler = self.handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }

        try:
            result = asyncio.run(handler(params))

            latency = (time.perf_counter() - start) * 1000
            self.request_count += 1
            self.total_latency += latency

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request_id
            }

    def run(self):
        """Main loop: read from stdin, write to stdout"""
        version = getattr(self._adapter, "version", "2.0.0") if self._adapter else "2.0.0"
        print(f"[claw-mem bridge] Starting v{version}...", file=sys.stderr)
        print(f"[claw-mem bridge] Python version: {sys.version}", file=sys.stderr)

        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

                if not self.running:
                    break

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                    "id": None
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": None
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

        print(f"[claw-mem bridge] Shutting down...", file=sys.stderr)
        print(f"[claw-mem bridge] Total requests: {self.request_count}", file=sys.stderr)
        if self.request_count > 0:
            avg_latency = self.total_latency / self.request_count
            print(f"[claw-mem bridge] Average latency: {avg_latency:.3f}ms", file=sys.stderr)


def main():
    """Entry point"""
    bridge = ClawMemBridge()
    bridge.run()


if __name__ == "__main__":
    main()
