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
from typing import Any, Dict, Optional

from claw_mem.adapters import AdapterRegistry


class ClawMemBridge:
    """JSON-RPC Bridge for claw-mem"""

    def __init__(self):
        self.request_count = 0
        self.total_latency = 0.0
        self.memory_manager = None
        self._adapter = None
        self._initialize()

    def _initialize(self):
        """Initialize MemoryManager and version-detected adapter."""
        import io
        _saved_stdout = sys.stdout
        sys.stdout = io.StringIO()
        init_ok = False
        try:
            try:
                from claw_mem import MemoryManager
                workspace = os.environ.get('OPENCLAW_WORKSPACE', os.getcwd())
                self.memory_manager = MemoryManager(workspace=workspace)
                self._adapter = AdapterRegistry.create_adapter(self.memory_manager)
                init_ok = True
            except Exception as e:
                self._respond(0, {"status": "error", "error": str(e)}, -32000)
                raise
        finally:
            sys.stdout = _saved_stdout

        if init_ok:
            self._respond(0, self._adapter.get_initialize_response())

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
            # Plugin Slots handlers
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
        return {"results": self._adapter.search(params)}

    def _handle_store(self, params: Dict) -> Dict:
        return self._adapter.store(params)

    def _handle_get(self, params: Dict) -> Dict:
        return self._adapter.get(params)

    def _handle_delete(self, params: Dict) -> Dict:
        return self._adapter.delete(params)

    def _handle_ping(self, params: Dict) -> Dict:
        return self._adapter.ping()

    def _handle_status(self, params: Dict) -> Dict:
        return self._adapter.status()

    def _handle_build_context(self, params: Dict) -> Dict:
        return self._adapter.build_context(params)

    def _handle_start_session(self, params: Dict) -> Dict:
        return self._adapter.start_session(params)

    def _handle_end_session(self, params: Dict) -> Dict:
        return self._adapter.end_session(params)

    def _handle_resolve_flush_plan(self, params: Dict) -> Dict:
        return self._adapter.resolve_flush_plan(params)

    # ---- main loop ------------------------------------------------------

    def run(self):
        """Main loop: read JSON-RPC lines from stdin, respond on stdout."""
        version = getattr(self._adapter, "version", "unknown")
        self._log(f"Starting {version}...")

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
