#!/usr/bin/env python3
"""
claw-mem Bridge Prototype - Phase 0 Verification

Purpose: Verify stdio JSON-RPC performance
- Mock claw-mem implementation
- stdio JSON-RPC server
- Performance measurement
"""

import sys
import json
import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MockMemory:
    """Mock memory item"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class MockMemoryManager:
    """Mock MemoryManager for performance testing"""
    
    def __init__(self):
        self.memories: Dict[str, MockMemory] = {}
        self.next_id = 1
    
    async def search(self, query: str, limit: int = 10) -> list:
        """Mock search - simulate 1-3ms latency"""
        # Simulate processing time (SQLite search)
        await asyncio.sleep(0.001)  # 1ms base latency
        
        # Return mock results
        results = []
        for i in range(min(limit, 3)):
            memory_id = f"mock-{i}"
            results.append(MockMemory(
                id=memory_id,
                content=f"Mock memory {i} for query: {query}",
                score=0.9 - i * 0.1,
                metadata={"source": "mock"}
            ))
        
        return results
    
    async def store(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Mock store - simulate 2-5ms latency"""
        # Simulate processing time (SQLite write)
        await asyncio.sleep(0.002)  # 2ms base latency
        
        # Create mock memory
        memory_id = f"mock-{self.next_id}"
        self.next_id += 1
        
        self.memories[memory_id] = MockMemory(
            id=memory_id,
            content=text,
            score=1.0,
            metadata=metadata or {}
        )
        
        return memory_id
    
    async def get(self, memory_id: str) -> Optional[MockMemory]:
        """Mock get - simulate 1-2ms latency"""
        # Simulate processing time
        await asyncio.sleep(0.001)  # 1ms base latency
        
        return self.memories.get(memory_id)
    
    async def delete(self, memory_id: str) -> bool:
        """Mock delete - simulate 1-2ms latency"""
        # Simulate processing time
        await asyncio.sleep(0.001)  # 1ms base latency
        
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False


class ClawMemBridgePrototype:
    """JSON-RPC Bridge for claw-mem (Prototype)"""
    
    def __init__(self):
        self.manager = MockMemoryManager()
        self.request_count = 0
        self.total_latency = 0.0
        self.running = True
        
        # Register handlers
        self.handlers = {
            "initialize": self._initialize,
            "search": self._search,
            "store": self._store,
            "get": self._get,
            "delete": self._delete,
            "shutdown": self._shutdown,
            "stats": self._stats,
        }
    
    async def _initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the bridge"""
        return {
            "status": "initialized",
            "version": "0.1.0-prototype",
            "mode": "mock"
        }
    
    async def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories"""
        query = params.get("query", "")
        limit = params.get("limit", 10)
        user_id = params.get("user_id", "default")
        
        start = time.perf_counter()
        results = await self.manager.search(query, limit)
        latency = (time.perf_counter() - start) * 1000  # ms
        
        return {
            "memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "score": m.score,
                    "metadata": m.metadata
                }
                for m in results
            ],
            "latency_ms": round(latency, 3),
            "query": query
        }
    
    async def _store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store a memory"""
        text = params.get("text", "")
        metadata = params.get("metadata", {})
        user_id = params.get("user_id", "default")
        
        start = time.perf_counter()
        memory_id = await self.manager.store(text, metadata)
        latency = (time.perf_counter() - start) * 1000  # ms
        
        return {
            "id": memory_id,
            "latency_ms": round(latency, 3)
        }
    
    async def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific memory"""
        memory_id = params.get("id")
        
        start = time.perf_counter()
        memory = await self.manager.get(memory_id)
        latency = (time.perf_counter() - start) * 1000  # ms
        
        if memory:
            return {
                "id": memory.id,
                "content": memory.content,
                "metadata": memory.metadata,
                "latency_ms": round(latency, 3)
            }
        else:
            return {
                "error": "Memory not found",
                "latency_ms": round(latency, 3)
            }
    
    async def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a memory"""
        memory_id = params.get("id")
        
        start = time.perf_counter()
        success = await self.manager.delete(memory_id)
        latency = (time.perf_counter() - start) * 1000  # ms
        
        return {
            "success": success,
            "latency_ms": round(latency, 3)
        }
    
    async def _shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown the bridge"""
        self.running = False
        return {"status": "shutdown"}
    
    async def _stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0
        
        return {
            "request_count": self.request_count,
            "total_latency_ms": round(self.total_latency, 3),
            "avg_latency_ms": round(avg_latency, 3)
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
                "id": request_id,
                "latency_ms": round(latency, 3)
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": request_id
            }
    
    def run(self):
        """Main loop: read from stdin, write to stdout"""
        # Log to stderr (don't pollute stdout)
        print("[claw-mem bridge prototype] Starting...", file=sys.stderr)
        print(f"[claw-mem bridge prototype] Python version: {sys.version}", file=sys.stderr)
        
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
        print(f"[claw-mem bridge prototype] Shutting down...", file=sys.stderr)
        print(f"[claw-mem bridge prototype] Total requests: {self.request_count}", file=sys.stderr)
        if self.request_count > 0:
            avg_latency = self.total_latency / self.request_count
            print(f"[claw-mem bridge prototype] Average latency: {avg_latency:.3f}ms", file=sys.stderr)


def main():
    """Entry point"""
    bridge = ClawMemBridgePrototype()
    bridge.run()


if __name__ == "__main__":
    main()
