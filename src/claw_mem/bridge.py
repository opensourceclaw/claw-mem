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
            # v2.13.0: Critical rules
            "get_critical_rules": self._handle_get_critical_rules,
            "store_critical_rule": self._handle_store_critical_rule,
            "delete_critical_rule": self._handle_delete_critical_rule,
            "build_index": self._handle_build_index,
            # P0: Retrieval Optimization + Proactive Injection
            "query_understanding": self._handle_query_understanding,
            "multi_strategy_retrieve": self._handle_multi_strategy_retrieve,
            "learning_to_rank": self._handle_learning_to_rank,
            "proactive_injection": self._handle_proactive_injection,
            "recognize_intent": self._handle_recognize_intent,
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

    def _handle_build_index(self, params: Dict) -> Dict:
        """Build in-memory search index."""
        if not self.memory_manager:
            return {"success": False, "error": "Memory manager not initialized"}
        try:
            self.memory_manager.build_index()
            return {
                "success": True,
                "index_built": self.memory_manager.index.built,
                "episodic_count": self.memory_manager.episodic.count(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---- P0 handlers: Retrieval Optimization + Proactive Injection -----

    def _handle_query_understanding(self, params: Dict) -> Dict:
        """P0: Query understanding — expansion + intent + entities."""
        from claw_mem.retrieval.query_understanding import QueryUnderstanding
        qu = QueryUnderstanding()
        query = params.get("query", "")
        context = params.get("context")
        expanded = qu.understand(query, context)
        return {
            "original": expanded.original,
            "expanded_text": expanded.expanded_text,
            "intent": expanded.intent.value,
            "entities": expanded.entities,
            "confidence": expanded.confidence,
        }

    def _handle_multi_strategy_retrieve(self, params: Dict) -> Dict:
        """P0: Multi-strategy retrieval — BM25 + Graph + Temporal."""
        from claw_mem.retrieval.query_understanding import QueryUnderstanding
        from claw_mem.retrieval.multi_strategy_retriever import MultiStrategyRetriever

        query_text = params.get("query", "")
        memories = params.get("memories", [])
        top_k = params.get("top_k", 10)

        # Step 1: Understand query
        qu = QueryUnderstanding()
        expanded = qu.understand(query_text)

        # Step 2: Multi-strategy retrieve
        retriever = MultiStrategyRetriever()
        result = retriever.retrieve(expanded, memories, top_k=top_k)

        return {
            "candidates": [c.to_dict() for c in result.candidates],
            "total_candidates": result.total_candidates,
            "strategies_used": result.strategies_used,
            "latency_ms": result.latency_ms,
        }

    def _handle_learning_to_rank(self, params: Dict) -> Dict:
        """P0: ML-based re-ranking."""
        from claw_mem.retrieval.query_understanding import QueryUnderstanding
        from claw_mem.retrieval.multi_strategy_retriever import Candidate
        from claw_mem.retrieval.learning_to_rank import LearningToRankReranker

        query_text = params.get("query", "")
        candidates_data = params.get("candidates", [])
        top_k = params.get("top_k", 10)

        # Build candidates
        candidates = [
            Candidate(
                memory_id=c.get("memory_id", ""),
                content=c.get("content", ""),
                score=c.get("score", 0.0),
                source_strategy=c.get("source_strategy", "unknown"),
                metadata=c.get("metadata", {}),
            )
            for c in candidates_data
        ]

        qu = QueryUnderstanding()
        expanded = qu.understand(query_text)

        reranker = LearningToRankReranker()
        results = reranker.rerank(expanded, candidates, top_k=top_k)

        return {
            "results": [r.to_dict() for r in results],
            "count": len(results),
        }

    def _handle_proactive_injection(self, params: Dict) -> Dict:
        """P0: Proactive memory injection."""
        from claw_mem.proactive_injection import (
            IntentRecognizer, MemoryTriggerDetector,
            InjectionManager, InjectionConfig,
            ScoredMemory,
        )

        message = params.get("message", "")
        memories = params.get("memories", [])
        token_budget = params.get("token_budget", 500)
        threshold = params.get("relevance_threshold", 0.7)

        # Step 1: Recognize intent
        recognizer = IntentRecognizer()
        intent = recognizer.recognize(message)

        # Step 2: Detect triggers
        detector = MemoryTriggerDetector()
        triggers = detector.detect_triggers(intent)

        # Step 3: Convert to ScoredMemory
        scored = [
            ScoredMemory(
                memory_id=m.get("id", m.get("memory_id", "")),
                content=m.get("content", ""),
                score=m.get("score", 0.0),
                timestamp=m.get("timestamp", ""),
                access_count=m.get("access_count", 0),
                memory_type=m.get("memory_type", "episodic"),
                tags=m.get("tags", []),
            )
            for m in memories
        ]

        # Step 4: Decide injection
        config = InjectionConfig(
            token_budget=token_budget,
            relevance_threshold=threshold,
            max_memories=params.get("max_memories", 5),
        )
        manager = InjectionManager(config)
        decision = manager.should_inject(scored)

        return {
            "should_inject": decision.should_inject,
            "formatted_text": decision.formatted_text,
            "memory_count": len(decision.memories),
            "token_count": decision.token_count,
            "intent_type": intent.intent_type.value,
            "entities": intent.entities,
            "triggers": [{"type": t.trigger_type.value, "query": t.search_query} for t in triggers],
        }

    def _handle_recognize_intent(self, params: Dict) -> Dict:
        """P0: Recognize user intent from message."""
        from claw_mem.proactive_injection import IntentRecognizer

        message = params.get("message", "")
        recognizer = IntentRecognizer()
        result = recognizer.recognize(message)

        return {
            "intent_type": result.intent_type.value,
            "entities": result.entities,
            "memory_needs": [n.value for n in result.memory_needs],
            "confidence": result.confidence,
        }

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
