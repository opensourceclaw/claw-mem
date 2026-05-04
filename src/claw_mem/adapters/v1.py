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
V1Strategy: OpenClaw v1.x backward-compatible adapter strategy.

Simplified behaviors:
- Flat context building (no LayeredContextFormatter)
- Placeholder flush plan (static thresholds)
- {id, content, score} search result format (no metadata)
"""

from datetime import datetime as dt
from typing import Any, Dict

from .base import BaseAdapter


class V1Strategy(BaseAdapter):
    """Strategy for OpenClaw v1.x (backward-compatible)."""

    def get_version(self) -> str:
        return "2.0.0"

    def get_initialize_response(self) -> Dict:
        return {"status": "initialized", "version": "2.0.0"}

    def format_search_result(self, result: Any) -> Dict:
        r = result if isinstance(result, dict) else vars(result) if hasattr(result, "__dict__") else {}
        return {
            "id": r.get("id", getattr(result, "id", getattr(result, "memory_id", "")) if not isinstance(result, dict) else ""),
            "content": r.get("content", getattr(result, "content", "") if not isinstance(result, dict) else ""),
            "score": r.get("score", getattr(result, "score", 0.0) if not isinstance(result, dict) else 0.0),
        }

    def build_context(self, memory_manager: Any, params: Dict) -> Dict:
        """Simplified flat context builder — no LayeredContextFormatter."""
        try:
            top_k = params.get("topK", 10)
            query = params.get("query", "important recent context")

            results = memory_manager.search(query=query, limit=top_k)

            if not results:
                return {"context": [], "count": 0}

            from claw_mem.context_injection import format_memory_context
            context_str = format_memory_context(results, max_length=4000)

            return {
                "context": [context_str] if context_str else [],
                "count": len(results),
            }
        except Exception as e:
            return {"context": [], "count": 0, "error": str(e)}

    def resolve_flush_plan(self, memory_manager: Any, params: Dict) -> Dict:
        """Simplified flush plan with placeholder static thresholds."""
        try:
            ts = dt.now().strftime("%Y%m%d-%H%M%S")
            return {
                "softThresholdTokens": 100000,
                "forceFlushTranscriptBytes": 500000,
                "reserveTokensFloor": 20000,
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
                "totalMemories": 0,
            }
        except Exception as e:
            return {"error": str(e)}
