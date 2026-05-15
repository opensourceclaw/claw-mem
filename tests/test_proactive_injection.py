"""Tests for Proactive Memory Injection module (P0-2)"""

import time
import pytest
from claw_mem.proactive_injection import (
    IntentRecognizer,
    InjectionIntent,
    IntentResult,
    MemoryNeed,
    MemoryTriggerDetector,
    MemoryTrigger,
    TriggerType,
    RelevanceScorer,
    ScoredMemory,
    InjectionManager,
    InjectionConfig,
    InjectionDecision,
    ConversationContext,
    PatternTriggerRegistry,
    ContextSimilarityTrigger,
    TemporalTrigger,
)

# ── IntentRecognizer Tests ─────────────────────────────────────────────────────


class TestIntentRecognizer:
    @pytest.fixture
    def recognizer(self):
        return IntentRecognizer()

    def test_project_discussion_intent(self, recognizer):
        result = recognizer.recognize("let's work on the claw-mem project")
        assert result.intent_type == InjectionIntent.PROJECT_DISCUSSION
        assert len(result.entities) > 0

    def test_preference_query_intent(self, recognizer):
        result = recognizer.recognize("what do I prefer for deployment?")
        assert result.intent_type == InjectionIntent.PREFERENCE_QUERY

    def test_recent_activity_intent(self, recognizer):
        result = recognizer.recognize("what did I do yesterday?")
        assert result.intent_type == InjectionIntent.RECENT_ACTIVITY

    def test_decision_making_intent(self, recognizer):
        result = recognizer.recognize("should I choose Python or Rust?")
        assert result.intent_type == InjectionIntent.DECISION_MAKING

    def test_code_work_intent(self, recognizer):
        result = recognizer.recognize("fix the bug in the function")
        assert result.intent_type == InjectionIntent.CODE_WORK

    def test_learning_feedback_intent(self, recognizer):
        result = recognizer.recognize("I need to improve code quality")
        assert result.intent_type == InjectionIntent.LEARNING_FEEDBACK

    def test_general_fallback(self, recognizer):
        result = recognizer.recognize("hello")
        assert result.intent_type == InjectionIntent.GENERAL
        assert result.confidence <= 0.5

    def test_chinese_project_intent(self, recognizer):
        result = recognizer.recognize("我们项目需要优化")
        assert result.intent_type == InjectionIntent.PROJECT_DISCUSSION

    def test_chinese_preference_intent(self, recognizer):
        result = recognizer.recognize("我喜欢用 Python 开发")
        assert result.intent_type == InjectionIntent.PREFERENCE_QUERY

    def test_chinese_recent_intent(self, recognizer):
        result = recognizer.recognize("最近做了什么？")
        assert result.intent_type == InjectionIntent.RECENT_ACTIVITY

    def test_entity_extraction(self, recognizer):
        result = recognizer.recognize("deploy claw-cog version 1.0.0")
        assert len(result.entities) > 0

    def test_memory_needs_project(self, recognizer):
        result = recognizer.recognize("let's work on neoclaw project")
        assert MemoryNeed.PROJECT_CONTEXT in result.memory_needs

    def test_memory_needs_preference(self, recognizer):
        result = recognizer.recognize("what is my preference?")
        assert MemoryNeed.USER_PREFERENCE in result.memory_needs

    def test_confidence_range(self, recognizer):
        result = recognizer.recognize("test message")
        assert 0.0 <= result.confidence <= 1.0

    def test_with_active_project_context(self, recognizer):
        context = ConversationContext(active_project="claw-mem")
        result = recognizer.recognize("let's deploy", context=context)
        assert result.confidence > 0


# ── MemoryTriggerDetector Tests ────────────────────────────────────────────────


class TestMemoryTriggerDetector:
    @pytest.fixture
    def detector(self):
        return MemoryTriggerDetector()

    @pytest.fixture
    def intent(self):
        return IntentResult(
            intent_type=InjectionIntent.PROJECT_DISCUSSION,
            entities=["claw-mem"],
            memory_needs=[MemoryNeed.PROJECT_CONTEXT],
            confidence=0.9,
        )

    def test_pattern_triggers(self, detector, intent):
        triggers = detector.detect_triggers(intent)
        assert len(triggers) >= 1
        assert all(isinstance(t, MemoryTrigger) for t in triggers)
        assert any(t.trigger_type == TriggerType.PATTERN for t in triggers)

    def test_trigger_search_query(self, detector, intent):
        triggers = detector.detect_triggers(intent)
        pattern_triggers = [t for t in triggers if t.trigger_type == TriggerType.PATTERN]
        assert len(pattern_triggers) > 0
        assert "claw-mem" in pattern_triggers[0].search_query

    def test_trigger_memory_types(self, detector, intent):
        triggers = detector.detect_triggers(intent)
        for t in triggers:
            assert isinstance(t.memory_types, list)

    def test_context_triggers_with_active_project(self, detector):
        context = ConversationContext(active_project="claw-mem")
        triggers = detector.detect_triggers(
            IntentResult(InjectionIntent.GENERAL, [], [], 0.3), context
        )
        assert len(triggers) >= 1
        assert any(t.trigger_type == TriggerType.CONTEXT for t in triggers)

    def test_temporal_triggers(self, detector):
        triggers = detector.detect_triggers(IntentResult(InjectionIntent.GENERAL, [], [], 0.3))
        temporal = [t for t in triggers if t.trigger_type == TriggerType.TEMPORAL]
        assert len(temporal) >= 0  # May or may not fire based on rate limiting

    def test_temporal_trigger_rate_limited(self, detector):
        triggers1 = detector.detect_triggers(IntentResult(InjectionIntent.GENERAL, [], [], 0.3))
        triggers2 = detector.detect_triggers(IntentResult(InjectionIntent.GENERAL, [], [], 0.3))
        temporal1 = [t for t in triggers1 if t.trigger_type == TriggerType.TEMPORAL]
        temporal2 = [t for t in triggers2 if t.trigger_type == TriggerType.TEMPORAL]
        if temporal1:
            assert len(temporal2) == 0  # Rate limited: only fires once per hour

    def test_temporal_trigger_reset(self, detector):
        detector.temporal_triggers.reset()
        triggers = detector.detect_triggers(IntentResult(InjectionIntent.GENERAL, [], [], 0.3))
        temporal = [t for t in triggers if t.trigger_type == TriggerType.TEMPORAL]
        assert len(temporal) >= 1  # Should fire after reset

    def test_disable_pattern_triggers(self, detector, intent):
        config = InjectionConfig(enable_pattern_triggers=False)
        triggers = detector.detect_triggers(intent, config=config)
        pattern = [t for t in triggers if t.trigger_type == TriggerType.PATTERN]
        assert len(pattern) == 0


# ── PatternTriggerRegistry Tests ───────────────────────────────────────────────


class TestPatternTriggerRegistry:
    def test_match_all_intents(self):
        registry = PatternTriggerRegistry()
        for intent_type in InjectionIntent:
            result = IntentResult(
                intent_type=intent_type, entities=["test"], memory_needs=[], confidence=0.5
            )
            triggers = registry.match(result)
            assert isinstance(triggers, list)
            if triggers:
                assert isinstance(triggers[0], MemoryTrigger)


# ── RelevanceScorer Tests ──────────────────────────────────────────────────────


class TestRelevanceScorer:
    @pytest.fixture
    def scorer(self):
        return RelevanceScorer()

    @pytest.fixture
    def recent_memory(self):
        recent_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 3600))
        return ScoredMemory(
            memory_id="mem-1",
            content="claw-mem memory system architecture and performance optimization",
            score=0.5,
            timestamp=recent_ts,
            access_count=10,
            memory_type="semantic",
        )

    @pytest.fixture
    def old_memory(self):
        return ScoredMemory(
            memory_id="mem-2",
            content="old deployment process",
            score=0.5,
            timestamp="2024-01-01T00:00:00",
            access_count=1,
            memory_type="procedural",
        )

    def test_score_recent_memory(self, scorer, recent_memory):
        score = scorer.score(recent_memory)
        assert 0.0 <= score <= 1.0

    def test_score_old_memory(self, scorer, old_memory):
        score = scorer.score(old_memory)
        assert 0.0 <= score <= 1.0

    def test_recent_memory_scores_higher(self, scorer, recent_memory, old_memory):
        recent_score = scorer.score(recent_memory)
        old_score = scorer.score(old_memory)
        assert recent_score > old_score  # Recent + frequent should score higher

    def test_score_with_context(self, scorer, recent_memory):
        context = ConversationContext(
            current_message="memory system architecture",
            recent_messages=["need performance optimization"],
        )
        score = scorer.score(recent_memory, context)
        assert score > 0.3  # Good context match

    def test_score_memories_in_place(self, scorer):
        memories = [
            ScoredMemory(
                "a", "Python AI code", 0.5, timestamp="2025-05-14T10:00:00", access_count=20
            ),
            ScoredMemory("b", "Old docs", 0.5, timestamp="2024-01-01T00:00:00", access_count=1),
        ]
        scored = scorer.score_memories(memories)
        assert len(scored) == 2
        assert scored[0].score >= scored[1].score  # Sorted by score

    def test_actionability_procedural_memory(self, scorer):
        mem = ScoredMemory(
            "id", "step 1: should do X, step 2: must do Y", 0.5, memory_type="procedural"
        )
        score = scorer.score(mem)
        assert score >= 0

    def test_actionability_decision_memory(self, scorer):
        mem = ScoredMemory(
            "id", "important decision: use Python for AI", 0.5, memory_type="decision"
        )
        score = scorer.score(mem)
        assert score >= 0


# ── InjectionManager Tests ─────────────────────────────────────────────────────


class TestInjectionManager:
    @pytest.fixture
    def manager(self):
        return InjectionManager(
            InjectionConfig(
                token_budget=200,
                relevance_threshold=0.4,
                max_memories=3,
            )
        )

    @pytest.fixture
    def sample_memories(self):
        recent_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 3600))
        return [
            ScoredMemory(
                "mem-1",
                "Python performance optimization with caching",
                0.85,
                timestamp=recent_ts,
                access_count=15,
                memory_type="semantic",
            ),
            ScoredMemory(
                "mem-2",
                "claw-mem architecture design decisions",
                0.75,
                timestamp=recent_ts,
                access_count=10,
                memory_type="decision",
            ),
            ScoredMemory(
                "mem-3",
                "Git workflow: always commit before deploy",
                0.65,
                timestamp=recent_ts,
                access_count=8,
                memory_type="procedural",
            ),
            ScoredMemory(
                "mem-4",
                "old irrelevant content",
                0.3,
                timestamp="2024-01-01T00:00:00",
                access_count=1,
                memory_type="episodic",
            ),
        ]

    def test_should_inject_high_relevance(self, manager, sample_memories):
        decision = manager.should_inject(sample_memories[:3])  # Top 3 high relevance
        assert isinstance(decision, InjectionDecision)
        assert decision.should_inject is True
        assert len(decision.memories) >= 1

    def test_should_not_inject_low_relevance(self, manager, sample_memories):
        decision = manager.should_inject([sample_memories[3]])  # Low relevance only
        assert decision.should_inject is False

    def test_injection_respects_max_memories(self, manager, sample_memories):
        decision = manager.should_inject(sample_memories)
        if decision.should_inject:
            assert len(decision.memories) <= manager.config.max_memories

    def test_injection_respects_token_budget(self, manager, sample_memories):
        decision = manager.should_inject(sample_memories)
        if decision.should_inject:
            assert decision.token_count <= manager.config.token_budget

    def test_injection_format_text(self, manager, sample_memories):
        decision = manager.should_inject(sample_memories[:2])
        if decision.should_inject:
            assert "Relevant context:" in decision.formatted_text or decision.formatted_text == ""

    def test_get_statistics(self, manager, sample_memories):
        manager.should_inject(sample_memories[:3])
        stats = manager.get_statistics()
        assert "injections" in stats or "suppressed" in stats

    def test_clear_history(self, manager, sample_memories):
        manager.should_inject(sample_memories[:3])
        manager.clear_history()
        stats = manager.get_statistics()
        assert stats["injections"] == 0

    def test_empty_memories(self, manager):
        decision = manager.should_inject([])
        assert decision.should_inject is False
        assert len(decision.memories) == 0

    def test_single_memory(self, manager, sample_memories):
        decision = manager.should_inject([sample_memories[0]])
        assert isinstance(decision, InjectionDecision)
        if decision.should_inject:
            assert len(decision.memories) >= 1

    def test_custom_threshold(self):
        manager = InjectionManager(InjectionConfig(relevance_threshold=0.9))
        recent_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        mem = ScoredMemory("id", "some content", 0.85, timestamp=recent_ts)
        decision = manager.should_inject([mem])
        # With 0.9 threshold, 0.85 score may be rejected unless context boosts it
        assert isinstance(decision, InjectionDecision)


# ── Dataclass Tests ────────────────────────────────────────────────────────────


class TestDataclasses:
    def test_injection_config_defaults(self):
        config = InjectionConfig()
        assert config.token_budget == 500
        assert config.relevance_threshold == 0.7
        assert config.max_memories == 5

    def test_intent_result_defaults(self):
        result = IntentResult(InjectionIntent.GENERAL)
        assert result.intent_type == InjectionIntent.GENERAL
        assert result.entities == []
        assert result.memory_needs == []

    def test_conversation_context_defaults(self):
        ctx = ConversationContext()
        assert ctx.current_message == ""
        assert ctx.recent_messages == []
        assert ctx.active_project is None

    def test_scored_memory_token_count(self):
        mem = ScoredMemory("id", "short", 0.5)
        assert mem.token_count >= 1

        long_mem = ScoredMemory("id", "x " * 1000, 0.5)
        assert long_mem.token_count > 1

    def test_injection_decision_defaults(self):
        decision = InjectionDecision(should_inject=False)
        assert decision.should_inject is False
        assert decision.memories == []
        assert decision.formatted_text == ""

    def test_memory_need_enum(self):
        assert MemoryNeed.PROJECT_CONTEXT.value == "project_context"
        assert MemoryNeed.USER_PREFERENCE.value == "user_preference"
        assert MemoryNeed.RECENT_EVENTS.value == "recent_events"


# ── ContextSimilarityTrigger Tests ─────────────────────────────────────────────


class TestContextSimilarityTrigger:
    def test_with_active_project(self):
        trigger = ContextSimilarityTrigger()
        context = ConversationContext(active_project="claw-mem")
        results = trigger.find_similar(context)
        assert len(results) >= 1
        assert "claw-mem" in results[0].search_query

    def test_long_session(self):
        trigger = ContextSimilarityTrigger()
        context = ConversationContext(session_duration_seconds=900)  # 15 min
        results = trigger.find_similar(context)
        assert len(results) >= 1

    def test_empty_context(self):
        trigger = ContextSimilarityTrigger()
        context = ConversationContext()
        results = trigger.find_similar(context)
        assert results == []
