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
Proactive Memory Injection (P0-2)

Intent-aware memory injection pipeline that proactively identifies and
injects relevant memories before the user explicitly asks.

Pipeline:
1. Intent Recognition → classify user intent, extract entities
2. Trigger Detection → pattern/context/temporal triggers
3. Relevance Scoring → context similarity + recency + frequency + actionability
4. Injection Decision → threshold check + token budget + format selection

Target: injection relevance >80%, token overhead <500 tokens
"""

import math
import re
import time
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


# ── Data Types ─────────────────────────────────────────────────────────────────

class InjectionIntent(Enum):
    """Recognized user intent types for proactive injection."""
    PROJECT_DISCUSSION = "project_discussion"
    PREFERENCE_QUERY = "preference_query"
    RECENT_ACTIVITY = "recent_activity"
    DECISION_MAKING = "decision_making"
    CODE_WORK = "code_work"
    DEPLOYMENT = "deployment"
    LEARNING_FEEDBACK = "learning_feedback"
    GENERAL = "general"


class MemoryNeed(Enum):
    """Types of memory that may be needed."""
    PROJECT_CONTEXT = "project_context"
    USER_PREFERENCE = "user_preference"
    RECENT_EVENTS = "recent_events"
    PAST_DECISIONS = "past_decisions"
    PROCEDURAL_KNOWLEDGE = "procedural_knowledge"
    TECHNICAL_REFERENCE = "technical_reference"


class TriggerType(Enum):
    """Types of memory triggers."""
    PATTERN = "pattern"      # Keyword/entity pattern match
    CONTEXT = "context"      # Context similarity
    TEMPORAL = "temporal"    # Time-based trigger


@dataclass
class InjectionConfig:
    """Configuration for proactive memory injection."""
    token_budget: int = 500
    relevance_threshold: float = 0.7
    max_memories: int = 5
    enable_pattern_triggers: bool = True
    enable_context_triggers: bool = True
    enable_temporal_triggers: bool = True
    injection_position: str = "before_response"


@dataclass
class IntentResult:
    """Result of intent recognition."""
    intent_type: InjectionIntent
    entities: List[str] = field(default_factory=list)
    memory_needs: List[MemoryNeed] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ConversationContext:
    """Conversation context for trigger detection."""
    current_message: str = ""
    recent_messages: List[str] = field(default_factory=list)
    active_project: Optional[str] = None
    session_duration_seconds: float = 0.0


@dataclass
class MemoryTrigger:
    """A detected memory trigger."""
    trigger_type: TriggerType
    search_query: str
    memory_types: List[str] = field(default_factory=list)
    max_results: int = 5
    recency_filter: Optional[str] = None  # "last_7_days", "last_30_days", etc.


@dataclass
class ScoredMemory:
    """A memory with relevance score."""
    memory_id: str
    content: str
    score: float
    timestamp: Optional[str] = None
    access_count: int = 0
    memory_type: str = "episodic"
    tags: List[str] = field(default_factory=list)
    token_count: int = 0

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = max(1, len(self.content) // 4)


@dataclass
class InjectionDecision:
    """Decision on what memories to inject."""
    should_inject: bool
    memories: List[ScoredMemory] = field(default_factory=list)
    formatted_text: str = ""
    token_count: int = 0
    reason: str = ""


# ── Intent Recognizer ──────────────────────────────────────────────────────────

class IntentRecognizer:
    """Recognize user intent and memory needs from messages.

    Uses pattern matching with bilingual (EN+ZH) patterns to identify
    user intent and determine what memories might be relevant.
    """

    INTENT_PATTERNS: Dict[InjectionIntent, List[str]] = {
        InjectionIntent.PROJECT_DISCUSSION: [
            r"(?i)\b(project|repo|repository)\b",
            r"(代码|项目|仓库|优化)",
            r"(claw-\w+|openclaw|neoclaw|devclaw|workclaw|deepclaw)",
        ],
        InjectionIntent.PREFERENCE_QUERY: [
            r"(?i)\b(prefer|preference|favorite|like)\b",
            r"(喜欢|习惯|偏好|想要)",
        ],
        InjectionIntent.RECENT_ACTIVITY: [
            r"(?i)\b(recent|yesterday|today)\b",
            r"(?i)\b(last time)\b",
            r"(最近|上次|昨天|今天)",
        ],
        InjectionIntent.DECISION_MAKING: [
            r"(?i)\b(decide|decision|plan)\b",
            r"(决定|选择|choose|决策|计划)",
        ],
        InjectionIntent.CODE_WORK: [
            r"(?i)\b(function|class|module|bug|fix|refactor|test|commit|push)\b",
            r"(函数|类|模块|测试|提交|修复)",
        ],
        InjectionIntent.DEPLOYMENT: [
            r"(?i)\b(deploy|release|tag|version)\b",
            r"(发布|部署|版本)",
        ],
        InjectionIntent.LEARNING_FEEDBACK: [
            r"(?i)\b(feedback)\b",
            r"(?i)\b(improve\s+(?:code|quality)|remember)\b",
            r"(记下|记下来)",
        ],
    }

    # Mapping intent → relevant memory needs
    INTENT_TO_MEMORY_NEEDS: Dict[InjectionIntent, List[MemoryNeed]] = {
        InjectionIntent.PROJECT_DISCUSSION: [
            MemoryNeed.PROJECT_CONTEXT, MemoryNeed.TECHNICAL_REFERENCE,
            MemoryNeed.PROCEDURAL_KNOWLEDGE,
        ],
        InjectionIntent.PREFERENCE_QUERY: [
            MemoryNeed.USER_PREFERENCE,
        ],
        InjectionIntent.RECENT_ACTIVITY: [
            MemoryNeed.RECENT_EVENTS,
        ],
        InjectionIntent.DECISION_MAKING: [
            MemoryNeed.PAST_DECISIONS, MemoryNeed.PROJECT_CONTEXT,
        ],
        InjectionIntent.CODE_WORK: [
            MemoryNeed.PROCEDURAL_KNOWLEDGE, MemoryNeed.TECHNICAL_REFERENCE,
            MemoryNeed.PROJECT_CONTEXT,
        ],
        InjectionIntent.DEPLOYMENT: [
            MemoryNeed.PROCEDURAL_KNOWLEDGE, MemoryNeed.PROJECT_CONTEXT,
        ],
        InjectionIntent.LEARNING_FEEDBACK: [
            MemoryNeed.PAST_DECISIONS, MemoryNeed.USER_PREFERENCE,
        ],
        InjectionIntent.GENERAL: [
            MemoryNeed.RECENT_EVENTS,
        ],
    }

    def __init__(self):
        self._compiled: Dict[InjectionIntent, List[re.Pattern]] = {}
        for intent, pat_list in self.INTENT_PATTERNS.items():
            self._compiled[intent] = [re.compile(p) for p in pat_list]

    def recognize(self, message: str,
                  context: Optional[ConversationContext] = None) -> IntentResult:
        """Recognize intent from message and optional context.

        Args:
            message: User message text
            context: Optional conversation context

        Returns:
            IntentResult with intent type, entities, and memory needs
        """
        # Score each intent by pattern matches
        scores: Dict[InjectionIntent, int] = {}
        for intent, patterns in self._compiled.items():
            matches = sum(1 for p in patterns if p.search(message))
            if matches > 0:
                scores[intent] = matches

        # Extract entities
        entities = self._extract_entities(message)

        # Determine best intent
        if not scores:
            best_intent = InjectionIntent.GENERAL
            confidence = 0.3
        else:
            best_intent = max(scores, key=scores.get)
            total_matches = sum(scores.values())
            confidence = min(1.0, scores[best_intent] / max(total_matches, 1))

        # Boost confidence if context aligns
        if context and context.active_project:
            confidence *= 1.2

        # Determine memory needs
        memory_needs = self.INTENT_TO_MEMORY_NEEDS.get(best_intent, [])

        return IntentResult(
            intent_type=best_intent,
            entities=entities,
            memory_needs=memory_needs,
            confidence=min(1.0, confidence),
        )

    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        entities: Set[str] = set()

        # System/project names
        project_pattern = re.compile(r'(?i)\b(claw-\w+|openclaw|neoclaw|devclaw|workclaw|deepclaw)\b')
        entities.update(project_pattern.findall(text))

        # Version numbers
        version_pattern = re.compile(r'[vV]?(\d+\.\d+(?:\.\d+)?(?:[a-z]\d*)?)')
        entities.update(version_pattern.findall(text))

        # Capitalized names (likely entities)
        name_pattern = re.compile(r'\b([A-Z][a-z]+)\b')
        for match in name_pattern.findall(text):
            if len(match) > 2:
                entities.add(match.lower())

        return list(entities)


# ── Memory Trigger Detector ────────────────────────────────────────────────────

class MemoryTriggerDetector:
    """Detect when memory should be proactively injected.

    Uses three trigger types:
    1. Pattern triggers: keyword/entity-based
    2. Context triggers: similarity to previous contexts
    3. Temporal triggers: time-based (standup, review, etc.)
    """

    def __init__(self):
        self.pattern_triggers = PatternTriggerRegistry()
        self.context_triggers = ContextSimilarityTrigger()
        self.temporal_triggers = TemporalTrigger()

    def detect_triggers(self, intent: IntentResult,
                        context: Optional[ConversationContext] = None,
                        config: Optional[InjectionConfig] = None) -> List[MemoryTrigger]:
        """Detect memory triggers based on intent and context.

        Args:
            intent: Recognized intent result
            context: Optional conversation context
            config: Injection configuration

        Returns:
            List of MemoryTrigger objects
        """
        cfg = config or InjectionConfig()
        triggers: List[MemoryTrigger] = []

        # Pattern triggers
        if cfg.enable_pattern_triggers:
            triggers.extend(self.pattern_triggers.match(intent))

        # Context triggers
        if cfg.enable_context_triggers and context:
            triggers.extend(self.context_triggers.find_similar(context))

        # Temporal triggers
        if cfg.enable_temporal_triggers:
            triggers.extend(self.temporal_triggers.check())

        return triggers


class PatternTriggerRegistry:
    """Registry of pattern-based memory triggers.

    Maps intent+entity combinations to memory search actions.
    """

    # Intent → (search_query_template, memory_types, max_results, recency_filter)
    PATTERN_TO_ACTION: Dict[InjectionIntent, Tuple[str, List[str], int, str]] = {
        InjectionIntent.PROJECT_DISCUSSION: (
            "project:{entities}",
            ["preference", "decision", "procedure", "semantic"],
            3,
            "last_30_days",
        ),
        InjectionIntent.PREFERENCE_QUERY: (
            "category:preference",
            ["preference"],
            5,
            None,
        ),
        InjectionIntent.RECENT_ACTIVITY: (
            "*",
            ["episode", "decision", "semantic"],
            5,
            "last_7_days",
        ),
        InjectionIntent.DECISION_MAKING: (
            "decision:{entities}",
            ["decision", "preference"],
            3,
            "last_30_days",
        ),
        InjectionIntent.CODE_WORK: (
            "code:{entities}",
            ["procedure", "semantic"],
            3,
            "last_30_days",
        ),
        InjectionIntent.DEPLOYMENT: (
            "deploy:{entities}",
            ["procedure", "decision"],
            3,
            "last_30_days",
        ),
        InjectionIntent.LEARNING_FEEDBACK: (
            "preference:{entities}",
            ["preference", "episode"],
            3,
            "last_30_days",
        ),
        InjectionIntent.GENERAL: (
            "*",
            ["episode", "semantic"],
            3,
            "last_7_days",
        ),
    }

    def match(self, intent: IntentResult) -> List[MemoryTrigger]:
        """Generate triggers from intent pattern match.

        Args:
            intent: Recognized intent

        Returns:
            List of pattern-based MemoryTrigger objects
        """
        action = self.PATTERN_TO_ACTION.get(intent.intent_type)
        if not action:
            return []

        template, mem_types, max_results, recency = action
        query = template.replace("{entities}", " ".join(intent.entities))

        return [MemoryTrigger(
            trigger_type=TriggerType.PATTERN,
            search_query=query,
            memory_types=mem_types,
            max_results=max_results,
            recency_filter=recency,
        )]


class ContextSimilarityTrigger:
    """Context-based trigger: find similar contexts from history."""

    def find_similar(self, context: ConversationContext) -> List[MemoryTrigger]:
        """Find similar contexts that warrant memory injection.

        Currently checks for:
        - Active project: inject project context
        - Extended session: inject recent decisions and preferences

        Args:
            context: Current conversation context

        Returns:
            List of context-based triggers
        """
        triggers = []

        if context.active_project:
            triggers.append(MemoryTrigger(
                trigger_type=TriggerType.CONTEXT,
                search_query=f"project:{context.active_project}",
                memory_types=["decision", "preference", "procedure"],
                max_results=3,
            ))

        if context.session_duration_seconds > 600:  # 10+ minutes
            triggers.append(MemoryTrigger(
                trigger_type=TriggerType.CONTEXT,
                search_query="*",
                memory_types=["preference", "semantic"],
                max_results=2,
                recency_filter="last_30_days",
            ))

        return triggers


class TemporalTrigger:
    """Time-based triggers for periodic memory injection."""

    def __init__(self):
        self._last_triggered: Dict[str, float] = {}

    def check(self) -> List[MemoryTrigger]:
        """Check if any temporal triggers should fire.

        Currently supports:
        - Hourly context refresh (every 60 min)
        - Not implemented: daily standup, weekly review

        Returns:
            List of temporal triggers
        """
        now = time.time()

        # Rate-limit temporal triggers (max once per hour)
        last = self._last_triggered.get("hourly_refresh", 0)
        if now - last < 3600:
            return []

        self._last_triggered["hourly_refresh"] = now

        return [MemoryTrigger(
            trigger_type=TriggerType.TEMPORAL,
            search_query="*",
            memory_types=["episode", "semantic"],
            max_results=2,
            recency_filter="last_7_days",
        )]

    def reset(self):
        """Reset trigger timers."""
        self._last_triggered.clear()


# ── Relevance Scorer ───────────────────────────────────────────────────────────

class RelevanceScorer:
    """Score relevance of memories for proactive injection.

    Scoring factors:
    - Context similarity (40%): How well memory matches current context
    - Recency (30%): How recent is the memory
    - Access frequency (20%): How often was it accessed
    - Actionability (10%): Can this memory be acted upon?
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "context_similarity": 0.40,
            "recency": 0.30,
            "frequency": 0.20,
            "actionability": 0.10,
        }

    def score(self, memory: ScoredMemory,
              context: Optional[ConversationContext] = None) -> float:
        """Score a memory for relevance.

        Args:
            memory: Memory to score
            context: Current conversation context

        Returns:
            Relevance score 0.0-1.0
        """
        context_score = self._compute_context_similarity(memory, context)
        recency_score = self._compute_recency_score(memory.timestamp)
        frequency_score = self._compute_frequency_score(memory.access_count)
        actionability_score = self._compute_actionability(memory, context)

        weighted = (
            self.weights["context_similarity"] * context_score +
            self.weights["recency"] * recency_score +
            self.weights["frequency"] * frequency_score +
            self.weights["actionability"] * actionability_score
        )

        return min(1.0, weighted)

    def score_memories(self, memories: List[ScoredMemory],
                       context: Optional[ConversationContext] = None) -> List[ScoredMemory]:
        """Score multiple memories in-place.

        Args:
            memories: List of ScoredMemory objects
            context: Current conversation context

        Returns:
            Same memories with updated scores
        """
        for mem in memories:
            mem.score = self.score(mem, context)
        return sorted(memories, key=lambda m: m.score, reverse=True)

    def _compute_context_similarity(
        self, memory: ScoredMemory, context: Optional[ConversationContext]
    ) -> float:
        """Compute similarity between memory and current context."""
        if not context:
            return 0.5
        context_text = context.current_message
        if context.recent_messages:
            context_text += " " + " ".join(context.recent_messages[-2:])

        if not context_text:
            return 0.5

        # Simple word overlap similarity
        mem_words = set(memory.content.lower().split())
        ctx_words = set(context_text.lower().split())

        if not mem_words or not ctx_words:
            return 0.5

        intersection = mem_words & ctx_words
        return len(intersection) / max(len(ctx_words), 1)

    @staticmethod
    def _compute_recency_score(timestamp_str: Optional[str]) -> float:
        """Compute recency score (0-1, 1 = very recent)."""
        if not timestamp_str:
            return 0.3
        try:
            ts = int(time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%dT%H:%M:%S")))
        except (ValueError, TypeError):
            try:
                ts = int(time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S")))
            except (ValueError, TypeError):
                return 0.3

        age_hours = max(0, time.time() - ts) / 3600
        # Half-life ~48 hours
        return math.exp(-math.log(2) * age_hours / 48)

    @staticmethod
    def _compute_frequency_score(access_count: int) -> float:
        """Compute frequency score (0-1)."""
        if access_count <= 0:
            return 0.0
        return min(1.0, math.log(access_count + 1) / math.log(101))

    @staticmethod
    def _compute_actionability(
        memory: ScoredMemory, context: Optional[ConversationContext]
    ) -> float:
        """Compute how actionable this memory is."""
        content = memory.content.lower()
        score = 0.3  # Base score

        # Boost for actionable keywords
        actionable_keywords = [
            "should", "must", "need to", "action", "step", "步骤",
            "需要", "必须", "配置", "设置", "config", "setup", "important",
        ]
        matches = sum(1 for kw in actionable_keywords if kw in content)
        if matches > 0:
            score = min(1.0, 0.3 + 0.15 * matches)

        # Boost for procedural memories (how-to content)
        if memory.memory_type == "procedural":
            score = min(1.0, score + 0.2)

        # Boost for decision-type memories (past decisions are actionable)
        if memory.memory_type == "decision" or "decision" in content:
            score = min(1.0, score + 0.1)

        return score


# ── Injection Manager ──────────────────────────────────────────────────────────

class InjectionManager:
    """Manage memory injection decisions.

    Decides what to inject based on relevance, token budget,
    and diversity constraints.
    """

    def __init__(self, config: Optional[InjectionConfig] = None):
        self.config = config or InjectionConfig()
        self.scorer = RelevanceScorer()
        self._injection_history: List[InjectionDecision] = []
        self._stats = {"injections": 0, "suppressed": 0, "total_tokens": 0}

    def should_inject(
        self,
        memories: List[ScoredMemory],
        context: Optional[ConversationContext] = None,
    ) -> InjectionDecision:
        """Decide what memories to inject.

        Args:
            memories: Scored memories to consider
            context: Current conversation context

        Returns:
            InjectionDecision with selected memories and formatted text
        """
        config = self.config

        # Score and sort
        scored = self.scorer.score_memories(memories, context)

        # Select memories respecting token budget and relevance threshold
        selected: List[ScoredMemory] = []
        tokens_used = 0

        for memory in scored:
            if memory.score < config.relevance_threshold:
                continue
            if tokens_used + memory.token_count > config.token_budget:
                continue
            if len(selected) >= config.max_memories:
                break

            selected.append(memory)
            tokens_used += memory.token_count

        should = len(selected) > 0

        if should:
            self._stats["injections"] += 1
            self._stats["total_tokens"] += tokens_used
            formatted = self._format_for_injection(selected)
        else:
            self._stats["suppressed"] += 1
            formatted = ""

        decision = InjectionDecision(
            should_inject=should,
            memories=selected,
            formatted_text=formatted,
            token_count=tokens_used,
            reason=f"Selected {len(selected)}/{len(memories)} memories with "
                   f"threshold {config.relevance_threshold}",
        )

        self._injection_history.append(decision)
        return decision

    def _format_for_injection(self, memories: List[ScoredMemory]) -> str:
        """Format selected memories for injection into prompt.

        Args:
            memories: Selected ScoredMemory objects

        Returns:
            Formatted string for prompt injection
        """
        if not memories:
            return ""

        lines = ["Relevant context:"]
        seen = set()

        for i, mem in enumerate(memories):
            if mem.content in seen:
                continue
            seen.add(mem.content)

            score_pct = int(mem.score * 100)
            lines.append(f"  [{mem.memory_type}] (relevance: {score_pct}%)")
            # Truncate long content
            content = mem.content[:300]
            if len(mem.content) > 300:
                content += "..."
            lines.append(f"    {content}")

        return "\n".join(lines) + "\n"

    def get_statistics(self) -> Dict:
        """Get injection manager statistics."""
        return {
            **self._stats,
            "history_length": len(self._injection_history),
            "config": {
                "token_budget": self.config.token_budget,
                "relevance_threshold": self.config.relevance_threshold,
                "max_memories": self.config.max_memories,
            },
        }

    def clear_history(self):
        """Clear injection history."""
        self._injection_history.clear()
        self._stats = {"injections": 0, "suppressed": 0, "total_tokens": 0}


__all__ = [
    'IntentRecognizer',
    'MemoryTriggerDetector',
    'RelevanceScorer',
    'InjectionManager',
    'InjectionConfig',
    'InjectionDecision',
    'IntentResult',
    'ConversationContext',
    'MemoryTrigger',
    'ScoredMemory',
    'InjectionIntent',
    'MemoryNeed',
    'TriggerType',
    'PatternTriggerRegistry',
    'ContextSimilarityTrigger',
    'TemporalTrigger',
]
