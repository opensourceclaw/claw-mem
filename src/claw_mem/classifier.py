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
Content classifier for claw-mem session continuity.

Classifies conversation messages by type (decision, preference, task_context,
fact, chat) and assigns importance scores for memory persistence decisions.
"""

from dataclasses import dataclass
from typing import List, Literal

ContentType = Literal["decision", "preference", "task_context", "fact", "chat"]

# Detection patterns (EN + ZH)
DECISION_PATTERNS = [
    "let's use",
    "let us use",
    "we'll use",
    "we will use",
    "we'll go with",
    "we will go with",
    "we'll choose",
    "we will choose",
    "decide to",
    "decided to",
    "choose to",
    "chose to",
    "confirm",
    "confirmed",
    "final decision",
    "\u6211\u4eec\u9009\u62e9",
    "\u6211\u4eec\u51b3\u5b9a",
    "\u786e\u5b9a\u7528",
    "\u5c31\u9009",
    "\u5b9a\u4e86",
]

PREFERENCE_PATTERNS = [
    "i prefer",
    "i like",
    "i want",
    "i don't want",
    "my preference",
    "i usually",
    "i always",
    "i never",
    "\u6211\u559c\u6b22",
    "\u6211\u504f\u597d",
    "\u6211\u4e60\u60ef",
    "\u6211\u5e0c\u671b",
    "\u6211\u4e0d\u559c\u6b22",
    "\u6211\u7684\u504f\u597d",
    "\u6211\u7684\u4e60\u60ef\u662f",
]

TASK_CONTEXT_PATTERNS = [
    "we're building",
    "we are building",
    "we're working on",
    "we are working on",
    "the task is",
    "the project is",
    "our goal",
    "current task",
    "next step",
    "\u6211\u4eec\u5728\u505a",
    "\u6211\u4eec\u5728\u5f00\u53d1",
    "\u6211\u4eec\u5728\u6784\u5efa",
    "\u9879\u76ee\u662f",
    "\u4efb\u52a1\u662f",
    "\u76ee\u6807\u662f",
    "\u4e0b\u4e00\u6b65",
]

FACT_PATTERNS = [
    "important",
    "note that",
    "remember",
    "fyi",
    "key point",
    "takeaway",
    "lesson",
    "\u91cd\u8981",
    "\u8bb0\u4f4f",
    "\u6ce8\u610f",
    "\u5173\u952e",
    "\u6559\u8bad",
]

# Comprehensive detection rules with importance scores
DETECTION_RULES = {
    "decision": {
        "keywords": [
            "let's use",
            "let us use",
            "we'll use",
            "we will use",
            "we'll go with",
            "we will go with",
            "decide",
            "choose",
            "confirm",
            "agreed",
            "settled",
            "final",
            # Other language keywords
            "decided to",
            "decision is",
            "chose to",
            "going with",
            "picked",
            "selected",
            # ZH keywords
            "\u6211\u4eec\u9009\u62e9",
            "\u6211\u4eec\u51b3\u5b9a",
            "\u786e\u5b9a\u7528",
            "\u5c31\u9009",
            "\u5b9a\u4e86",
            "\u51b3\u5b9a",
            "\u9009\u62e9",
            "\u786e\u8ba4",
        ],
        "importance": 0.9,
    },
    "preference": {
        "keywords": [
            "prefer",
            "like",
            "want",
            "don't want",
            "my preference",
            "usually",
            "always",
            "never",
            "i'd rather",
            "i would rather",
            # ZH keywords
            "\u559c\u6b22",
            "\u504f\u597d",
            "\u4e60\u60ef",
            "\u5e0c\u671b",
            "\u4e0d\u559c\u6b22",
            "\u504f\u597d\u7684\u662f",
            "\u4e60\u60ef\u662f",
        ],
        "importance": 0.8,
    },
    "task_context": {
        "keywords": [
            "building",
            "working on",
            "creating",
            "developing",
            "task is",
            "project is",
            "goal",
            "next step",
            "current",
            "working on",
            # ZH keywords
            "\u5f00\u53d1",
            "\u6784\u5efa",
            "\u9879\u76ee",
            "\u4efb\u52a1",
            "\u76ee\u6807",
            "\u4e0b\u4e00\u6b65",
            "\u5728\u505a",
            "\u5728\u5f00\u53d1",
        ],
        "importance": 0.7,
    },
    "fact": {
        "keywords": [
            "important",
            "note",
            "remember",
            "fyi",
            "key point",
            "takeaway",
            "lesson",
            # ZH keywords
            "\u91cd\u8981",
            "\u8bb0\u4f4f",
            "\u6ce8\u610f",
            "\u5173\u952e",
            "\u6559\u8bad",
        ],
        "importance": 0.6,
    },
    "chat": {
        "keywords": [],
        "importance": 0.3,
    },
}


@dataclass
class ContentClassification:
    """Result of content classification."""

    type: ContentType
    importance: float  # 0.0 - 1.0
    should_save: bool
    reasoning: str


def classify_content(content: str) -> ContentClassification:
    """Classify a single content string by type and importance.

    Args:
        content: Text to classify.

    Returns:
        ContentClassification with type, importance, should_save, and reasoning.
    """
    if not content or not content.strip():
        return ContentClassification(
            type="chat",
            importance=0.0,
            should_save=False,
            reasoning="Empty content",
        )

    content_lower = content.lower()

    # Check content types in priority order
    for content_type in ["decision", "preference", "task_context", "fact"]:
        rules = DETECTION_RULES[content_type]
        for keyword in rules["keywords"]:
            if keyword in content_lower:
                return ContentClassification(
                    type=content_type,
                    importance=rules["importance"],
                    should_save=True,
                    reasoning=f"Matched keyword: '{keyword}'",
                )

    # Default: chat
    # Longer content is more likely to be meaningful
    importance = min(0.5, len(content) / 200.0)
    return ContentClassification(
        type="chat",
        importance=importance,
        should_save=False,
        reasoning=f"Default classification (length={len(content)})",
    )


def extract_important_content(messages: List[dict]) -> dict:
    """Extract important content from conversation messages.

    Args:
        messages: List of message dicts with 'role' and 'content'.

    Returns:
        Dict with 'important' list and 'count' of important items.
    """
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
            content = " ".join(str(c.get("text", "")) for c in content if isinstance(c, dict))
        if not content or not str(content).strip():
            continue
        content_str = str(content).strip()
        if len(content_str) < 10:
            continue

        classification = classify_content(content_str)
        results.append(
            {
                "content": content_str,
                "type": classification.type,
                "importance": classification.importance,
                "source": role,
            }
        )

    results.sort(key=lambda r: r["importance"], reverse=True)
    important = [r for r in results if r["importance"] >= 0.5]
    return {"important": important, "count": len(important)}


def generate_session_summary(messages: List[dict]) -> dict:
    """Generate a structured summary of the session.

    Args:
        messages: List of message dicts.

    Returns:
        Dict with summary containing overview, decisions, preferences, tasks, facts.
    """
    result = extract_important_content(messages)
    important = result.get("important", [])

    decisions = [r for r in important if r["type"] == "decision"]
    preferences = [r for r in important if r["type"] == "preference"]
    tasks = [r for r in important if r["type"] == "task_context"]
    facts = [r for r in important if r["type"] == "fact"]

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


def detect_content_type(content: str) -> dict:
    """Detect type and importance of a single content string.

    Args:
        content: Text to classify.

    Returns:
        Dict with 'type' and 'importance'.
    """
    classification = classify_content(content)
    return {
        "type": classification.type,
        "importance": classification.importance,
    }
