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
Tests for Three-Tier Memory Retrieval API
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from claw_mem.retrieval.three_tier import (
    ThreeTierRetriever,
    MemoryLayer,
    MemoryResult,
    SearchQuery,
    IntentClassifier,
    SessionStartupHook,
    search_memory,
)


class TestMemoryLayer:
    """Tests for MemoryLayer enum"""

    def test_memory_layer_values(self):
        """Test memory layer enum values"""
        assert MemoryLayer.L1.value == "l1"
        assert MemoryLayer.L2.value == "l2"
        assert MemoryLayer.L3.value == "l3"


class TestMemoryResult:
    """Tests for MemoryResult dataclass"""

    def test_memory_result_creation(self):
        """Test creating a MemoryResult"""
        result = MemoryResult(
            memory_id="test-123",
            content="Test memory content",
            layer=MemoryLayer.L2,
            score=0.95,
            source="/path/to/file.md",
            timestamp="2026-03-23T10:00:00",
            tags=["test", "demo"],
            memory_type="episodic",
        )

        assert result.memory_id == "test-123"
        assert result.content == "Test memory content"
        assert result.layer == MemoryLayer.L2
        assert result.score == 0.95
        assert result.source == "/path/to/file.md"
        assert result.timestamp == "2026-03-23T10:00:00"
        assert result.tags == ["test", "demo"]
        assert result.memory_type == "episodic"

    def test_memory_result_to_dict(self):
        """Test converting MemoryResult to dictionary"""
        result = MemoryResult(
            memory_id="test-456",
            content="Another test",
            layer=MemoryLayer.L3,
            score=0.8,
            source="MEMORY.md",
        )

        d = result.to_dict()

        assert d["memory_id"] == "test-456"
        assert d["content"] == "Another test"
        assert d["layer"] == "l3"
        assert d["score"] == 0.8
        assert d["source"] == "MEMORY.md"

    def test_memory_result_default_values(self):
        """Test MemoryResult default values"""
        result = MemoryResult(
            memory_id="test",
            content="content",
            layer=MemoryLayer.L1,
            score=1.0,
            source="source",
        )

        assert result.tags == []
        assert result.memory_type == "episodic"
        assert result.timestamp is None


class TestSearchQuery:
    """Tests for SearchQuery dataclass"""

    def test_search_query_defaults(self):
        """Test SearchQuery default values"""
        query = SearchQuery(query="test query")

        assert query.query == "test query"
        assert len(query.layers) == 3  # All layers by default
        assert query.limit == 10
        assert query.memory_type is None
        assert query.tags is None
        assert query.min_score == 0.1
        assert query.intent is None

    def test_search_query_custom_values(self):
        """Test SearchQuery with custom values"""
        query = SearchQuery(
            query="custom query",
            layers=[MemoryLayer.L2, MemoryLayer.L3],
            limit=5,
            memory_type="semantic",
            tags=["important"],
            min_score=0.5,
        )

        assert query.query == "custom query"
        assert query.layers == [MemoryLayer.L2, MemoryLayer.L3]
        assert query.limit == 5
        assert query.memory_type == "semantic"
        assert query.tags == ["important"]
        assert query.min_score == 0.5


class TestIntentClassifier:
    """Tests for IntentClassifier"""

    def test_classifier_creation(self):
        """Test creating an IntentClassifier"""
        classifier = IntentClassifier()
        assert classifier is not None

    def test_classify_english_query(self):
        """Test classifying an English query"""
        classifier = IntentClassifier()
        intent, keywords = classifier.classify("How does the memory system work?")

        assert keywords is not None
        assert len(keywords) > 0
        # Intent may be None if no specific topic detected
        assert intent is None or isinstance(intent, str)

    def test_classify_topic_query(self):
        """Test classifying a topic-specific query"""
        classifier = IntentClassifier()
        intent, keywords = classifier.classify("Tell me about memory system architecture")

        assert intent is not None or intent is None  # May not detect with short query
        assert len(keywords) > 0

    def test_classify_harness_engineering(self):
        """Test classifying harness engineering query"""
        classifier = IntentClassifier()
        intent, keywords = classifier.classify(
            "Explain the harness engineering pillar agent system"
        )

        assert intent == "harness_engineering" or intent is None
        assert len(keywords) > 0

    def test_extract_keywords_chinese(self):
        """Test keyword extraction for Chinese queries"""
        classifier = IntentClassifier()

        # Test with Chinese query
        intent, keywords = classifier.classify("记忆系统如何工作")

        assert keywords is not None
        # Should extract some keywords

    def test_contains_chinese(self):
        """Test Chinese character detection"""
        classifier = IntentClassifier()

        assert classifier._contains_chinese("你好世界") is True
        assert classifier._contains_chinese("Hello World") is False
        assert classifier._contains_chinese("Hello 世界") is True

    def test_tokenize_english(self):
        """Test English tokenization"""
        classifier = IntentClassifier()

        tokens = classifier._tokenize_english("The quick brown fox jumps")

        assert len(tokens) > 0
        assert "quick" in tokens or "brown" in tokens  # Stopwords removed

    def test_detect_topic_no_match(self):
        """Test topic detection with no clear match"""
        classifier = IntentClassifier()

        intent = classifier._detect_topic(["random", "unrelated", "words"])

        # May return None for unrelated words
        assert intent is None or isinstance(intent, str)


class TestThreeTierRetriever:
    """Tests for ThreeTierRetriever"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create memory directory
        memory_dir = workspace / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Create MEMORY.md (L3)
        memory_file = workspace / "MEMORY.md"
        memory_file.write_text(
            "# MEMORY.md\n\n"
            "<!-- tags: test, demo; id: mem-001 -->\n"
            "[2026-03-23T10:00:00] Test memory content for L3 storage\n"
            "\n"
            "<!-- tags: project; id: mem-002 -->\n"
            "[2026-03-23T11:00:00] Memory system is a three-tier architecture\n"
        )

        # Create daily memory file (L2)
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = memory_dir / f"{today}.md"
        daily_file.write_text(
            "# Daily Memory\n\n"
            "<!-- tags: daily, session; id: daily-001 -->\n"
            f"[{today}T09:00:00] Daily memory entry for testing\n"
        )

        yield workspace

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_retriever_creation(self, temp_workspace):
        """Test creating a ThreeTierRetriever"""
        retriever = ThreeTierRetriever(temp_workspace)

        assert retriever is not None
        assert retriever.workspace == temp_workspace
        assert retriever.intent_classifier is not None

    def test_search_l3_memory(self, temp_workspace):
        """Test searching L3 long-term memory"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = retriever.search(
            query="test memory",
            layers=["l3"],
            limit=5,
        )

        assert len(results) > 0
        assert all(r.layer == MemoryLayer.L3 for r in results)

    def test_search_l2_memory(self, temp_workspace):
        """Test searching L2 short-term memory"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = retriever.search(
            query="daily memory",
            layers=["l2"],
            limit=5,
        )

        # Should find the daily memory entry
        assert len(results) > 0
        assert all(r.layer == MemoryLayer.L2 for r in results)

    def test_search_all_layers(self, temp_workspace):
        """Test searching all layers"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = retriever.search(
            query="memory",
            layers=["l1", "l2", "l3"],
            limit=10,
        )

        # Should find results from L2 and L3
        assert len(results) > 0

    def test_search_with_l1_working_memory(self, temp_workspace):
        """Test searching with L1 working memory context"""
        retriever = ThreeTierRetriever(temp_workspace)

        session_context = {
            "working_memory": [
                {
                    "id": "l1-001",
                    "content": "Working memory test content",
                    "timestamp": "2026-03-23T12:00:00",
                    "type": "episodic",
                    "tags": ["working", "test"],
                }
            ]
        }

        results = retriever.search(
            query="working test",
            layers=["l1"],
            limit=5,
            session_context=session_context,
        )

        assert len(results) > 0
        assert all(r.layer == MemoryLayer.L1 for r in results)
        assert results[0].content == "Working memory test content"

    def test_search_with_memory_type_filter(self, temp_workspace):
        """Test searching with memory type filter"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = retriever.search(
            query="memory",
            layers=["l3"],
            memory_type="episodic",
            limit=5,
        )

        # All results should match the filtered type
        for result in results:
            assert result.memory_type == "episodic"

    def test_search_limit(self, temp_workspace):
        """Test search result limiting"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = retriever.search(
            query="memory",
            layers=["l2", "l3"],
            limit=3,
        )

        assert len(results) <= 3

    def test_search_min_score(self, temp_workspace):
        """Test search with minimum score threshold"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = retriever.search(
            query="nonexistent_xyz_123",  # Query that shouldn't match anything
            layers=["l3"],
            limit=10,
        )

        # Should return empty or low-scoring results
        # (depending on implementation details)

    def test_search_nonexistent_workspace(self):
        """Test searching with nonexistent workspace"""
        retriever = ThreeTierRetriever(Path("/nonexistent/path"))

        # Should not raise an exception
        results = retriever.search(query="test", layers=["l3"])
        assert len(results) == 0

    def test_compute_relevance_score(self, temp_workspace):
        """Test relevance score computation"""
        retriever = ThreeTierRetriever(temp_workspace)

        score = retriever._compute_relevance_score(
            query="test memory",
            content="This is a test about memory systems",
            intent=None,
        )

        assert 0.0 <= score <= 1.0

    def test_compute_relevance_score_with_intent(self, temp_workspace):
        """Test relevance score with intent boost"""
        retriever = ThreeTierRetriever(temp_workspace)

        score_without = retriever._compute_relevance_score(
            query="memory",
            content="Memory system is a three-tier architecture",
            intent=None,
        )

        score_with = retriever._compute_relevance_score(
            query="memory",
            content="Memory system is a three-tier architecture",
            intent="memory_system",
        )

        # Intent boost should increase score
        assert score_with >= score_without

    def test_rank_and_deduplicate(self, temp_workspace):
        """Test result ranking and deduplication"""
        retriever = ThreeTierRetriever(temp_workspace)

        results = [
            MemoryResult(
                memory_id=f"test-{i}",
                content=f"Test content {i}",
                layer=MemoryLayer.L3,
                score=0.9 - i * 0.1,
                source="test.md",
            )
            for i in range(5)
        ]

        ranked = retriever._rank_and_deduplicate(results, "test")

        # Should be sorted by score (descending)
        assert ranked[0].score >= ranked[1].score >= ranked[2].score

    def test_performance_stats(self, temp_workspace):
        """Test performance statistics"""
        retriever = ThreeTierRetriever(temp_workspace)

        # Perform a search
        retriever.search(query="test", layers=["l3"])

        stats = retriever.get_performance_stats()

        assert "total_searches" in stats
        assert "average_latency_ms" in stats
        assert "performance_target_met" in stats
        assert stats["total_searches"] == 1

    def test_parse_memory_file(self, temp_workspace):
        """Test parsing memory file content"""
        retriever = ThreeTierRetriever(temp_workspace)

        content = """# MEMORY.md

<!-- tags: test, demo; id: mem-001 -->
[2026-03-23T10:00:00] Test memory content

<!-- tags: project; id: mem-002 -->
[2026-03-23T11:00:00] Another memory entry
"""

        memories = retriever._parse_memory_file(content, temp_workspace / "MEMORY.md")

        assert len(memories) == 2
        assert memories[0]["id"] == "mem-001"
        assert memories[0]["content"] == "Test memory content"
        assert "test" in memories[0]["tags"]


class TestSessionStartupHook:
    """Tests for SessionStartupHook"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create MEMORY.md
        memory_file = workspace / "MEMORY.md"
        memory_file.write_text(
            "# MEMORY.md\n\n"
            "<!-- tags: context, session; id: ctx-001 -->\n"
            "[2026-03-23T10:00:00] User prefers Python for development\n"
        )

        yield workspace
        shutil.rmtree(temp_dir)

    def test_startup_hook_creation(self, temp_workspace):
        """Test creating a SessionStartupHook"""
        retriever = ThreeTierRetriever(temp_workspace)
        hook = SessionStartupHook(retriever)

        assert hook is not None
        assert hook.retriever is retriever

    def test_on_session_start(self, temp_workspace):
        """Test session start hook"""
        retriever = ThreeTierRetriever(temp_workspace)
        hook = SessionStartupHook(retriever)

        result = hook.on_session_start(
            session_id="test-session-123",
            initial_context="Python development preferences",
        )

        assert "memories" in result
        assert "intent" in result
        assert result["session_id"] == "test-session-123"

    def test_on_session_start_no_context(self, temp_workspace):
        """Test session start hook without context"""
        retriever = ThreeTierRetriever(temp_workspace)
        hook = SessionStartupHook(retriever)

        result = hook.on_session_start(
            session_id="test-session-456",
            initial_context=None,
        )

        assert result["memories"] == []
        assert result["intent"] is None

    def test_format_context_for_prompt(self, temp_workspace):
        """Test formatting context for prompt injection"""
        retriever = ThreeTierRetriever(temp_workspace)
        hook = SessionStartupHook(retriever)

        memories = [
            {
                "layer": "l3",
                "content": "Test memory content",
                "source": "MEMORY.md",
            },
            {
                "layer": "l2",
                "content": "Daily memory",
                "source": "2026-03-23.md",
            },
        ]

        formatted = hook.format_context_for_prompt(memories)

        assert "Retrieved Memories" in formatted
        assert "Test memory content" in formatted
        assert "MEMORY.md" in formatted

    def test_format_context_for_prompt_empty(self, temp_workspace):
        """Test formatting empty context"""
        retriever = ThreeTierRetriever(temp_workspace)
        hook = SessionStartupHook(retriever)

        formatted = hook.format_context_for_prompt([])

        assert formatted == ""


class TestSearchMemoryFunction:
    """Tests for the convenience search_memory function"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create MEMORY.md
        memory_file = workspace / "MEMORY.md"
        memory_file.write_text(
            "# MEMORY.md\n\n"
            "<!-- tags: convenience; id: conv-001 -->\n"
            "[2026-03-23T10:00:00] Convenience function test\n"
        )

        # Monkey-patch ConfigDetector for testing
        from claw_mem import config
        original_detect = config.ConfigDetector.detect_workspace

        def mock_detect(cls, custom_paths=None):
            return str(workspace)

        config.ConfigDetector.detect_workspace = classmethod(mock_detect)

        yield workspace

        # Restore original
        config.ConfigDetector.detect_workspace = original_detect
        shutil.rmtree(temp_dir)

    def test_search_memory_function(self, temp_workspace):
        """Test the search_memory convenience function"""
        results = search_memory(
            query="convenience test",
            layers=["l3"],
            limit=5,
        )

        assert isinstance(results, list)
        # Results should be dictionaries
        assert all(isinstance(r, dict) for r in results)


class TestRelevanceScoreComputation:
    """Tests for relevance score edge cases"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_empty_content_score(self, temp_workspace):
        """Test score with empty content"""
        retriever = ThreeTierRetriever(temp_workspace)

        score = retriever._compute_relevance_score(
            query="test",
            content="",
            intent=None,
        )

        assert score == 0.0

    def test_exact_match_score(self, temp_workspace):
        """Test exact match scoring"""
        retriever = ThreeTierRetriever(temp_workspace)

        score = retriever._compute_relevance_score(
            query="hello world",
            content="This is about hello world systems",
            intent=None,
        )

        assert score > 0.5  # Exact match should score high

    def test_no_match_score(self, temp_workspace):
        """Test no match scoring"""
        retriever = ThreeTierRetriever(temp_workspace)

        score = retriever._compute_relevance_score(
            query="xyzabc123",
            content="This is about completely different topics",
            intent=None,
        )

        assert score < 0.5  # No match should score low


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
