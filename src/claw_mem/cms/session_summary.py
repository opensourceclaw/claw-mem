# Copyright 2026 Peter Cheng
"""Session summary generator for CMS Phase 2 (v3.0.0-rc.2).

Extracts structured summaries from session memories using
keyword-based detection (decisions, preferences, actions).
"""

from typing import Dict, List, Optional
from .compression_result import SessionSummary


class SessionSummaryGenerator:
    """Generate structured summaries from session memories.

    Strategies:
      - key_points: Extract decisions, preferences, actions
      - chronological: Order by time, extract per-phase
      - semantic: Cluster by similarity
    """

    # Detection patterns
    _DECISION_KW = [
        "decide",
        "decided",
        "decision",
        "choose",
        "chose",
        "confirm",
        "agreed",
        "settled",
        "final",
        "we will",
        "we'll use",
        "决定",
        "选择",
        "确认",
        "确定",
        "定了",
    ]
    _PREFERENCE_KW = [
        "prefer",
        "preference",
        "like",
        "want",
        "don't want",
        "i usually",
        "i always",
        "i never",
        "喜欢",
        "偏好",
        "习惯",
        "希望",
        "不喜欢",
    ]
    _ACTION_KW = [
        "implement",
        "build",
        "create",
        "fix",
        "deploy",
        "test",
        "install",
        "configure",
        "setup",
        "migrate",
        "实现",
        "开发",
        "构建",
        "修复",
        "部署",
        "测试",
        "安装",
        "配置",
        "设置",
        "迁移",
    ]

    def generate(
        self, session_id: str, memories: List[Dict], strategy: str = "key_points"
    ) -> SessionSummary:
        """Generate a session summary.

        Args:
            session_id: Session identifier.
            memories: List of memory dicts with 'id' and 'content'.
            strategy: 'key_points' | 'chronological' | 'semantic'.

        Returns:
            SessionSummary with extracted decisions, preferences, actions.
        """
        if strategy == "key_points":
            return self._generate_key_points(session_id, memories)
        elif strategy == "chronological":
            return self._generate_chronological(session_id, memories)
        return self._generate_semantic(session_id, memories)

    def _generate_key_points(self, session_id: str, memories: List[Dict]) -> SessionSummary:
        decisions = self._extract_by_keywords(memories, self._DECISION_KW)
        preferences = self._extract_by_keywords(memories, self._PREFERENCE_KW)
        actions = self._extract_by_keywords(memories, self._ACTION_KW)

        overview = self._build_overview(memories, decisions, preferences, actions)
        token_count = sum(len(m.get("content", "").split()) for m in memories)

        return SessionSummary(
            session_id=session_id,
            overview=overview,
            decisions=decisions,
            preferences=preferences,
            actions=actions,
            token_count=token_count,
            memory_count=len(memories),
        )

    def _generate_chronological(self, session_id: str, memories: List[Dict]) -> SessionSummary:
        # Sort by time if available, otherwise use order
        items = []
        for i, m in enumerate(memories):
            content = m.get("content", "")
            items.append(f"[{i}] {content[:80]}")
        overview = "Chronological: " + "; ".join(items[:5])
        return SessionSummary(
            session_id=session_id,
            overview=overview,
            memory_count=len(memories),
            token_count=sum(len(m.get("content", "").split()) for m in memories),
        )

    def _generate_semantic(self, session_id: str, memories: List[Dict]) -> SessionSummary:
        return self._generate_key_points(session_id, memories)

    # ── Extraction helpers ────────────────────────────────────

    def _extract_by_keywords(self, memories: List[Dict], keywords: List[str]) -> List[str]:
        """Extract memory contents matching keywords."""
        results = []
        for m in memories:
            content = m.get("content", "")
            if not content:
                continue
            lower = content.lower()
            if any(kw in lower for kw in keywords):
                results.append(content[:200])
        return results[:10]

    def _build_overview(
        self, memories: List[Dict], decisions: List[str], preferences: List[str], actions: List[str]
    ) -> str:
        parts = []
        if actions:
            parts.append(f"Actions: {len(actions)} items")
        if decisions:
            parts.append(f"Decisions: {len(decisions)} items")
        if preferences:
            parts.append(f"Preferences: {len(preferences)} items")
        if not parts:
            parts.append(f"Session with {len(memories)} memories")
        return "; ".join(parts)
