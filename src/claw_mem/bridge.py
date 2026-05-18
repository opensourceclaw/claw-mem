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
from claw_mem.classifier import (  # noqa
    extract_important_content,
    generate_session_summary,
    detect_content_type as _detect_content_type_fn,
)


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

                workspace = os.environ.get("OPENCLAW_WORKSPACE", os.getcwd())
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
                "message": result if isinstance(result, str) else str(result),
            }
        else:
            response["result"] = result

        # Write directly to the real stdout fd, bypassing any wrappers
        line = json.dumps(response, ensure_ascii=False) + "\n"
        sys.__stdout__.write(line)
        sys.__stdout__.flush()

    def _log(self, msg: str):
        """Write diagnostic message to stderr.

        Note: TypeScript side already prepends [claw-mem bridge], so we omit it here
        to avoid double-prefix in logs.
        """
        print(msg, file=sys.stderr, flush=True)

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
            # v2.13.0: Critical rules
            "get_critical_rules": self._handle_get_critical_rules,
            "store_critical_rule": self._handle_store_critical_rule,
            "delete_critical_rule": self._handle_delete_critical_rule,
            # v2.13.x: Session continuity
            "extract_important_content": self._handle_extract_important_content,
            "generate_session_summary": self._handle_generate_session_summary,
            "detect_content_type": self._handle_detect_content_type,
            # v2.18.0: Compression spectrum
            "get_compression_stats": self._handle_get_compression_stats,
            "manual_compress": self._handle_manual_compress,
            "configure_compression": self._handle_configure_compression,
            # v3.0.0-rc.1: CMS Perception Layer
            "get_capacity_stats": self._handle_get_capacity_stats,
            "get_importance_scores": self._handle_get_importance_scores,
            "get_important_memories": self._handle_get_important_memories,
            # v3.0.0-rc.3: CMS Phase 3 State Machine
            "save_snapshot": self._handle_save_snapshot,
            "recover_session": self._handle_recover_session,
            "switch_context": self._handle_switch_context,
            "list_snapshots": self._handle_list_snapshots,
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

    def _handle_get_critical_rules(self, params: Dict) -> Dict:
        """v2.13.0: Get all critical rules."""
        if not self.memory_manager:
            return {"rules": [], "count": 0}
        rules = self.memory_manager.get_critical_rules()
        return {"rules": rules, "count": len(rules)}

    def _handle_store_critical_rule(self, params: Dict) -> Dict:
        """v2.13.0: Store a critical rule."""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not initialized"}
        rule_id = self.memory_manager.store_critical_rule(
            text=params.get("text", ""),
            metadata=params.get("metadata"),
        )
        return {"success": True, "rule_id": rule_id}

    def _handle_delete_critical_rule(self, params: Dict) -> Dict:
        """v2.13.0: Delete a critical rule."""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not initialized"}
        deleted = self.memory_manager.delete_critical_rule(params.get("rule_id", ""))
        return {"success": deleted}

    # ---- session continuity handlers (v2.13.x) --------------------------

    def _handle_extract_important_content(self, params: Dict) -> Dict:
        """Extract important content from messages with type classification."""
        return extract_important_content(params.get("messages", []))

    def _handle_generate_session_summary(self, params: Dict) -> Dict:
        """Generate structured summary from messages."""
        return generate_session_summary(params.get("messages", []))

    def _handle_detect_content_type(self, params: Dict) -> Dict:
        """Detect the type of a single content string."""
        content = params.get("content", "")
        if not content:
            return {"type": "chat", "importance": 0.0}
        return _detect_content_type_fn(str(content))

    # ---- v2.18.0: Compression spectrum handlers ------------------------

    def _handle_get_compression_stats(self, params: Dict) -> Dict:
        """Get compression spectrum statistics."""
        if not self.memory_manager:
            return {"enabled": False}
        return self.memory_manager.get_compression_stats()

    def _handle_manual_compress(self, params: Dict) -> Dict:
        """Manually trigger compression for a memory."""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not initialized"}
        result = self.memory_manager.manual_compress(params.get("memory_id", ""))
        return {"success": result is not None, "result": result}

    def _handle_configure_compression(self, params: Dict) -> Dict:
        """Runtime configuration of compression thresholds."""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not initialized"}
        cs = self.memory_manager.compression_spectrum
        if cs:
            cs.configure_thresholds(
                access=params.get("access"),
                apply=params.get("apply"),
                verify=params.get("verify"),
            )
            return {"success": True}
        return {"success": False, "error": "Compression not enabled"}

    # ---- v3.0.0-rc.1: CMS Perception Layer handlers --------------------

    def _handle_get_capacity_stats(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"enabled": False}
        stats = self.memory_manager.get_capacity_stats()
        return stats if stats else {"enabled": False}

    def _handle_get_importance_scores(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"error": "Memory manager not initialized"}
        ids = params.get("memory_ids", [])
        scores = self.memory_manager.get_importance_scores(ids)
        return {"scores": scores} if scores else {"error": "CMS not enabled"}

    def _handle_get_important_memories(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"error": "Memory manager not initialized"}
        important = self.memory_manager.get_important_memories(
            threshold=params.get("threshold", 0.5),
            limit=params.get("limit", 50),
        )
        return {"memories": important} if important else {"error": "CMS not enabled"}

    # ---- main loop ------------------------------------------------------

    # ---- v3.0.0-rc.3: CMS Phase 3 State Machine handlers -----------

    def _handle_save_snapshot(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"error": "Memory manager not initialized"}
        sid = params.get("session_id", "default")
        return {"snapshot_id": self.memory_manager.save_snapshot(sid)}

    def _handle_recover_session(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"error": "Memory manager not initialized"}
        result = self.memory_manager.recover_session(
            session_id=params.get("session_id", ""),
            snapshot_id=params.get("snapshot_id"),
            strategy=params.get("strategy", "latest"),
        )
        return result if result else {"error": "Recovery failed"}

    def _handle_switch_context(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"error": "Memory manager not initialized"}
        result = self.memory_manager.switch_context(
            from_id=params.get("from_id", ""),
            to_id=params.get("to_id", ""),
            strategy=params.get("strategy", "preserve_important"),
        )
        return result if result else {"error": "Switch failed"}

    def _handle_list_snapshots(self, params: Dict) -> Dict:
        if not self.memory_manager:
            return {"snapshots": []}
        return {
            "snapshots": self.memory_manager.list_snapshots(params.get("session_id", "default"))
        }

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
    # Ensure CLAW_MEM_SILENT is set to prevent diagnostic print() from
    # leaking into the JSON-RPC line protocol on stdout.
    if not os.environ.get("CLAW_MEM_SILENT"):
        os.environ["CLAW_MEM_SILENT"] = "1"
    bridge = ClawMemBridge()
    bridge.run()


if __name__ == "__main__":
    main()
