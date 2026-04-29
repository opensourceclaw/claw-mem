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
"""

import sys
import json
import os
from typing import Any, Dict, Optional

# Add src to path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


class ClawMemBridge:
    """JSON-RPC Bridge for claw-mem"""

    def __init__(self):
        self.request_id = 0
        self.memory_manager = None
        self._initialize()

    def _initialize(self):
        """Initialize MemoryManager"""
        try:
            from claw_mem import MemoryManager
            workspace = os.environ.get('OPENCLAW_WORKSPACE', os.getcwd())
            self.memory_manager = MemoryManager(workspace=workspace)
            self._respond(None, {"status": "ok", "message": "initialized"})
        except Exception as e:
            self._respond(None, {"error": str(e)}, -32000)

    def _respond(self, id: Any, result: Any, error_code: Optional[int] = None):
        """Send JSON-RPC response"""
        response = {
            "jsonrpc": "2.0",
            "id": id,
        }

        if error_code is not None:
            response["error"] = {
                "code": error_code,
                "message": result if isinstance(result, str) else str(result)
            }
        else:
            response["result"] = result

        print(json.dumps(response), flush=True)

    def _handle_request(self, request: Dict) -> Any:
        """Handle JSON-RPC request"""
        method = request.get("method")
        params = request.get("params", {})
        id = request.get("id")

        if not method:
            return self._respond(id, "Method not found", -32601)

        # Route to handler
        handlers = {
            "search": self._handle_search,
            "store": self._handle_store,
            "get": self._handle_get,
            "delete": self._handle_delete,
            "ping": self._handle_ping,
            "status": self._handle_status,
        }

        handler = handlers.get(method)
        if not handler:
            return self._respond(id, f"Method '{method}' not found", -32601)

        try:
            result = handler(params)
            return self._respond(id, result)
        except Exception as e:
            return self._respond(id, str(e), -32000)

    def _handle_search(self, params: Dict) -> Dict:
        """Handle search request"""
        query = params.get("query", "")
        top_k = params.get("topK", params.get("top_k", 10))
        memory_type = params.get("memory_type", "episodic")

        results = self.memory_manager.search(
            query=query,
            limit=top_k,
            memory_type=memory_type
        )

        return {
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

    def _handle_store(self, params: Dict) -> Dict:
        """Handle store request"""
        text = params.get("text", "")
        metadata = params.get("metadata", {})
        memory_type = params.get("memory_type", "episodic")

        memory_id = self.memory_manager.store(
            content=text,
            memory_type=memory_type,
            metadata=metadata
        )

        return {"id": memory_id, "status": "stored"}

    def _handle_get(self, params: Dict) -> Dict:
        """Handle get request"""
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
        """Handle delete request"""
        memory_id = params.get("id", "")

        success = self.memory_manager.delete(memory_id)
        return {"deleted": success}

    def _handle_ping(self, params: Dict) -> Dict:
        """Handle ping request"""
        return {"pong": True}

    def _handle_status(self, params: Dict) -> Dict:
        """Handle status request"""
        return {
            "status": "ok",
            "initialized": self.memory_manager is not None,
            "workspace": os.getcwd()
        }

    def run(self):
        """Run the bridge - read from stdin, write to stdout"""
        # Send ready message
        self._respond(0, {"ready": True})

        # Main loop
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                self._handle_request(request)
            except json.JSONDecodeError as e:
                self._respond(None, f"Invalid JSON: {e}", -32700)
            except Exception as e:
                self._respond(None, str(e), -32000)


def main():
    """Entry point"""
    bridge = ClawMemBridge()
    bridge.run()


if __name__ == "__main__":
    main()
