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
V2Strategy: OpenClaw v2.x adapter strategy.

Encapsulates version-specific behavior for the current (v2.x) OpenClaw:
- Tiered context building with LayeredContextFormatter
- Dynamic flush plan with threshold scaling
- {id, text, score, metadata} search result format
"""

from datetime import datetime as dt
from typing import Any, Dict

from .base import BaseAdapter


class V2Strategy(BaseAdapter):
    """Strategy for OpenClaw v2.x (current)."""

    def get_version(self) -> str:
        return "2.8.0"

    def get_initialize_response(self) -> Dict:
        return {"status": "ok", "message": "initialized", "version": "2.6.0"}

    def format_search_result(self, result: Any) -> Dict:
        r = result if isinstance(result, dict) else vars(result) if hasattr(result, "__dict__") else {}
        return {
            "id": r.get("id", getattr(result, "id", getattr(result, "memory_id", "")) if not isinstance(result, dict) else ""),
            "text": r.get("text", r.get("content", getattr(result, "content", getattr(result, "text", "")) if not isinstance(result, dict) else "")),
            "score": r.get("score", getattr(result, "score", 0) if not isinstance(result, dict) else 0),
            "metadata": r.get("metadata", getattr(result, "metadata", {}) if not isinstance(result, dict) else {}),
        }

    def build_context(self, memory_manager: Any, params: Dict) -> Dict:
        try:
            top_k = params.get("topK", 10)
            query = params.get("query", "")

            from claw_mem.context_injection import (
                format_memory_context,
                LayeredContextFormatter,
            )

            layered = LayeredContextFormatter()
            token_info = layered.token_report(query)

            results = memory_manager.search(
                query=query if query else "important recent context",
                limit=top_k,
            )

            if not results:
                return {
                    "context": [layered.format(query)],
                    "count": 0,
                    "token_info": token_info,
                }

            context_str = format_memory_context(results, max_length=4000)
            layer_context = layered.format(query)

            return {
                "context": [layer_context, context_str] if context_str else [layer_context],
                "count": len(results),
                "token_info": token_info,
            }
        except Exception as e:
            return {"context": [], "count": 0, "error": str(e)}

    def resolve_flush_plan(self, memory_manager: Any, params: Dict) -> Dict:
        try:
            stats = memory_manager.get_stats()
            total_memories = sum(
                stats.get(k, 0) for k in ("episodic", "semantic", "procedural")
                if isinstance(stats.get(k), (int, float))
            )

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
