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
        deleted = self.memory_manager.delete_critical_rule(
            params.get("rule_id", "")
        )
        return {"success": deleted}

    # ---- session continuity handlers (v2.13.x) --------------------------

    # Content type detection patterns (EN + ZH)
    _DECISION_PATTERNS = [
        "let's use", "let us use", "we'll use", "we will use",
        "we'll go with", "we will go with", "we'll choose", "we will choose",
        "decide to", "decided to", "choose to", "chose to",
        "confirm", "confirmed", "final decision",
        "我们选择", "我们决定", "确定用", "就选", "定了",
    ]
    _PREFERENCE_PATTERNS = [
        "i prefer", "i like", "i want", "i don't want",
        "my preference", "i usually", "i always", "i never",
        "我喜欢", "我偏好", "我习惯", "我希望", "我不喜欢",
        "我的偏好", "我的习惯是",
    ]
    _TASK_CONTEXT_PATTERNS = [
        "we're building", "we are building", "we're working on",
        "we are working on", "the task is", "the project is",
        "our goal", "current task", "next step",
        "我们在做", "我们在开发", "我们在构建", "项目是",
        "任务是", "目标是", "下一步",
    ]
    _FACT_PATTERNS = [
        "important", "note that", "remember", "fyi",
        "key point", "takeaway", "lesson",
        "重要", "记住", "注意", "关键", "教训",
    ]

    def _detect_content_type(self, content: str) -> Dict:
        """Classify content by type and importance score."""
        lower = content.lower()
        if any(p in lower for p in self._DECISION_PATTERNS):
            return {"type": "decision", "importance": 0.9}
        if any(p in lower for p in self._PREFERENCE_PATTERNS):
            return {"type": "preference", "importance": 0.8}
        if any(p in lower for p in self._TASK_CONTEXT_PATTERNS):
            return {"type": "task_context", "importance": 0.7}
        if any(p in lower for p in self._FACT_PATTERNS):
            return {"type": "fact", "importance": 0.6}
        # Longer content is more likely to be meaningful
        importance = min(0.5, len(content) / 200.0)
        return {"type": "chat", "importance": importance}

    def _handle_extract_important_content(self, params: Dict) -> Dict:
        """Extract important content from messages with type classification."""
        messages = params.get("messages", [])
        if not messages or not isinstance(messages, list):
            return {"important": [], "count": 0}

        results = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "")
            if role not in ("user", "assistant", "system"):
                continue
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    str(c.get("text", "")) for c in content if isinstance(c, dict)
                )
            if not content or not str(content).strip():
                continue
            content_str = str(content).strip()
            # Skip very short messages (<10 chars)
            if len(content_str) < 10:
                continue
            detected = self._detect_content_type(content_str)
            results.append({
                "content": content_str,
                "type": detected["type"],
                "importance": detected["importance"],
                "source": role,
            })
        results.sort(key=lambda r: r["importance"], reverse=True)
        important = [r for r in results if r["importance"] >= 0.5]
        return {"important": important, "count": len(important)}

    def _handle_generate_session_summary(self, params: Dict) -> Dict:
        """Generate structured summary from messages."""
        messages = params.get("messages", [])
        result = self._handle_extract_important_content({"messages": messages})
        important = result.get("important", [])

        decisions = [r for r in important if r["type"] == "decision"]
        preferences = [r for r in important if r["type"] == "preference"]
        tasks = [r for r in important if r["type"] == "task_context"]
        facts = [r for r in important if r["type"] == "fact"]

        # Build overview from first 3 important items
        overview_items = decisions[:1] + preferences[:1] + tasks[:1] + facts[:1]
        overview_parts = []
        for item in overview_items:
            overview_parts.append(f"[{item['type']}] {item['content'][:100]}")
        overview = "; ".join(overview_parts[:5]) if overview_parts else "No significant content"

        return {
            "summary": {
                "overview": overview,
                "decisions": [d["content"] for d in decisions],
                "preferences": [p["content"] for p in preferences],
                "tasks": [t["content"] for t in tasks],
                "facts": [f["content"] for f in facts],
                "total_messages": len(messages) if isinstance(messages, list) else 0,
                "important_count": len(important),
            },
        }

    def _handle_detect_content_type(self, params: Dict) -> Dict:
        """Detect the type of a single content string."""
        content = params.get("content", "")
        if not content:
            return {"type": "chat", "importance": 0.0}
        return self._detect_content_type(str(content))

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
    # Ensure CLAW_MEM_SILENT is set to prevent diagnostic print() from
    # leaking into the JSON-RPC line protocol on stdout.
    if not os.environ.get('CLAW_MEM_SILENT'):
        os.environ['CLAW_MEM_SILENT'] = '1'
    bridge = ClawMemBridge()
    bridge.run()


if __name__ == "__main__":
    main()
