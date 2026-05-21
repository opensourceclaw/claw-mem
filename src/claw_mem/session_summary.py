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

"""Session summary auto-save for /new and /reset commands.

Rule-based extraction of session summaries from working memory,
without external LLM calls. Saved to semantic memory for cross-session retrieval.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class SessionSummary:
    """Session summary for cross-session memory retrieval.

    Extracted from working memory messages using rule-based matching
    (no external LLM calls).
    """

    session_id: str
    timestamp: str
    summary: str
    topics: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)


# ── Detection patterns ──────────────────────────────────────────

_TODO_PATTERNS = [
    "- [ ]",
    "- [x]",
    "TODO",
    "todo",
    "待办",
    "要做",
    "需要实现",
    "需要完成",
    "需要做",
    "还需",
    "尚未",
]

_CONCLUSION_PATTERNS = [
    "结论",
    "决定",
    "确定",
    "最终方案",
    "总结",
    "总之",
    "conclusion",
    "decision",
    "decided",
    "agreed",
    "final",
    "we will",
    "plan is",
]

_TOPIC_DETECT = [
    "#",
    "主题",
    "topic",
]


# ── Public API ───────────────────────────────────────────────────

def extract_summary(messages: List[Dict]) -> SessionSummary:
    """Extract session summary from messages using rule-based matching.

    Args:
        messages: List of memory dicts with 'content', 'tags', 'session_id',
                  'timestamp' fields.

    Returns:
        SessionSummary with extracted tasks, conclusions, topics.
    """
    pending_tasks = _extract_todos(messages)
    key_points = _extract_conclusions(messages)
    topics = _extract_topics(messages)
    summary_text = _build_summary_text(messages)

    # Determine session_id and timestamp from messages
    if messages:
        session_id = messages[0].get("session_id", "unknown") or "unknown"
        timestamp = messages[-1].get("timestamp", "") or datetime.now().isoformat()
    else:
        session_id = "unknown"
        timestamp = datetime.now().isoformat()

    return SessionSummary(
        session_id=session_id,
        timestamp=timestamp,
        summary=summary_text,
        topics=topics,
        key_points=key_points,
        pending_tasks=pending_tasks,
    )


# ── Extraction helpers ───────────────────────────────────────────

def _extract_todos(messages: List[Dict]) -> List[str]:
    """Extract pending TODO items from messages."""
    todos = []
    for msg in messages:
        content = msg.get("content", "")
        if not content:
            continue
        for line in content.splitlines():
            line_stripped = line.strip()
            if not line_stripped:
                continue
            lower_line = line_stripped.lower()
            if any(pattern.lower() in lower_line for pattern in _TODO_PATTERNS):
                # Clean up the line: remove leading markers but keep content
                clean = line_stripped
                for prefix in ("- [ ] ", "- [x] ", "- ", "TODO:", "todo:", "待办:", "待办："):
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):].strip()
                if clean and clean not in todos:
                    todos.append(clean)
    return todos[:10]


def _extract_conclusions(messages: List[Dict]) -> List[str]:
    """Extract conclusions and decisions from messages."""
    conclusions = []
    for msg in messages:
        content = msg.get("content", "")
        if not content:
            continue
        for line in content.splitlines():
            line_stripped = line.strip()
            if not line_stripped:
                continue
            lower_line = line_stripped.lower()
            if any(pattern.lower() in lower_line for pattern in _CONCLUSION_PATTERNS):
                # Clean up common prefixes
                clean = line_stripped
                for prefix in ("结论:", "结论：", "决定:", "决定：", "总结:", "总结：",
                               "最终方案:", "最终方案：", "总之,", "总之，",
                               "Conclusion:", "Decision:"):
                    if clean.startswith(prefix):
                        clean = clean[len(prefix):].strip()
                if clean and clean not in conclusions:
                    conclusions.append(clean)
    return conclusions[:10]


def _extract_topics(messages: List[Dict]) -> List[str]:
    """Extract topics from message tags and content hashtags."""
    topics = []
    for msg in messages:
        # From tags
        for tag in msg.get("tags", []) or []:
            if tag and tag not in topics:
                topics.append(tag)
        # From content hashtags
        content = msg.get("content", "")
        for word in content.split():
            if word.startswith("#") and len(word) > 1:
                topic = word[1:].rstrip(".,;:!?）)")
                if topic not in topics:
                    topics.append(topic)
    return topics[:15]


def _build_summary_text(messages: List[Dict]) -> str:
    """Build summary text from the last 3 meaningful messages."""
    if not messages:
        return "Empty session"

    # Take last 3 messages with non-empty content
    meaningful = [m for m in messages if m.get("content", "").strip()]
    if not meaningful:
        return "No meaningful content"

    last_msgs = meaningful[-3:]
    parts = []
    for m in last_msgs:
        content = m.get("content", "")
        # Truncate each message to 120 chars
        if len(content) > 120:
            content = content[:117] + "..."
        parts.append(content)

    return "\n".join(parts)
