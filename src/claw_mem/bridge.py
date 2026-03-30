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

import os
import sys

# CRITICAL: Set silent mode BEFORE any other imports
# This must be done before importing memory_manager or storage modules
os.environ['CLAW_MEM_SILENT'] = '1'

import json
import asyncio
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Now import MemoryManager (it will see CLAW_MEM_SILENT=1)
from .memory_manager import MemoryManager


class ClawMemBridge:
    """JSON-RPC Bridge for claw-mem"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.manager: Optional[MemoryManager] = None
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
        }
    
    async def _initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MemoryManager with config"""
        start = time.perf_counter()
        
        try:
            # Initialize MemoryManager
            workspace = params.get("workspace_dir") or params.get("workspace") or self.config.get("workspace")
            
            # Create MemoryManager (auto-initializes on construction)
            self.manager = MemoryManager(workspace=workspace)
            
            latency = (time.perf_counter() - start) * 1000
            
            return {
                "status": "initialized",
                "version": "2.0.0",
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
            # MemoryManager doesn't have close method, just clear references
            self.retriever = None
            self.manager = None
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
            memory_type = params.get("memory_type")
            metadata = params.get("metadata")
            
            # Use MemoryManager.search
            results = self.manager.search(
                query=query,
                memory_type=memory_type,
                metadata=metadata,
                limit=limit
            )
            
            latency = (time.perf_counter() - start) * 1000
            
            # Format results
            memories = []
            for result in results:
                memories.append({
                    "id": result.get("id", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return {
                "memories": memories,
                "query": query,
                "count": len(memories),
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
            tags = params.get("tags", [])
            
            # Store using MemoryManager
            memory_id = self.manager.store(
                content=text,
                memory_type=memory_type,
                tags=tags,
                metadata=metadata
            )
            
            latency = (time.perf_counter() - start) * 1000
            
            return {
                "id": memory_id,
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
        """Get a specific memory - not supported by MemoryManager"""
        start = time.perf_counter()
        latency = (time.perf_counter() - start) * 1000
        
        return {
            "error": "MemoryManager does not support get() method. Use search() instead.",
            "latency_ms": round(latency, 3)
        }
    
    async def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a memory - not supported by MemoryManager"""
        start = time.perf_counter()
        latency = (time.perf_counter() - start) * 1000
        
        return {
            "error": "MemoryManager does not support delete() method.",
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
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        start = time.perf_counter()
        
        # Get handler
        handler = self.handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            }
        
        try:
            # Run async handler
            result = asyncio.run(handler(params))
            
            # Track latency
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
        # Log to stderr (don't pollute stdout)
        print(f"[claw-mem bridge] Starting v2.0.0...", file=sys.stderr)
        print(f"[claw-mem bridge] Python version: {sys.version}", file=sys.stderr)
        
        for line in sys.stdin:
            try:
                # Parse request
                request = json.loads(line.strip())
                
                # Handle request
                response = self.handle_request(request)
                
                # Write response
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
                # Check shutdown
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
        
        # Print final stats
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
