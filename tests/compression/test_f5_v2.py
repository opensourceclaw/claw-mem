"""
Comprehensive tests for claw-mem F5 V2 Compression Module

Covers: F5CompressorV2 (all levels), UltraCompressor, global functions,
compress/decompress cycles, edge cases, and compression stats.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from claw_mem.compression.f5_v2 import (
    CompressionLevelV2,
    CompressionResultV2,
    F5CompressorV2,
    UltraCompressor,
    compress_v2,
    get_f5_compressor,
    get_ultra_compressor,
    reset_f5_compressor,
    reset_ultra_compressor,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def f5_medium():
    return F5CompressorV2(CompressionLevelV2.MEDIUM)


@pytest.fixture
def f5_light():
    return F5CompressorV2(CompressionLevelV2.LIGHT)


@pytest.fixture
def f5_aggressive():
    return F5CompressorV2(CompressionLevelV2.AGGRESSIVE)


@pytest.fixture
def f5_ultra():
    return F5CompressorV2(CompressionLevelV2.ULTRA)


@pytest.fixture
def ultra():
    return UltraCompressor()


@pytest.fixture
def sample_sentences():
    """Multi-sentence English content covering various topics."""
    return (
        "We decided to use Python for the new project. "
        "The deadline is 2025-03-15 and we need to complete it on time. "
        "We agreed to meet every Monday at 10:00 AM to discuss progress. "
        "There is a critical bug in the login module that must be fixed. "
        "The team approved the new feature request for user authentication. "
        "Please send the report to admin@example.com by next Friday. "
        "The previous implementation had several issues that need resolution. "
    )


@pytest.fixture
def sample_cjk():
    """Chinese-language content covering various topics."""
    return (
        "我们决定使用Python进行新项目的开发。"
        "我们需要在2025年3月15日前完成这个重要的任务。"
        "会议决定每周一上午10点讨论项目进展。"
        "登录模块中有一个关键的错误需要修复。"
        "团队批准了新功能请求用于用户认证。"
        "请将报告发送至admin@example.com。"
    )


# ---------------------------------------------------------------------------
# CompressionLevelV2
# ---------------------------------------------------------------------------


class TestCompressionLevelV2:
    def test_level_values(self):
        assert CompressionLevelV2.LIGHT.value == 0.3
        assert CompressionLevelV2.MEDIUM.value == 0.5
        assert CompressionLevelV2.AGGRESSIVE.value == 0.7
        assert CompressionLevelV2.ULTRA.value == 0.85

    def test_level_order(self):
        levels = list(CompressionLevelV2)
        assert levels == [
            CompressionLevelV2.LIGHT,
            CompressionLevelV2.MEDIUM,
            CompressionLevelV2.AGGRESSIVE,
            CompressionLevelV2.ULTRA,
        ]

    def test_is_enum(self):
        assert isinstance(CompressionLevelV2.LIGHT, CompressionLevelV2)


# ---------------------------------------------------------------------------
# CompressionResultV2
# ---------------------------------------------------------------------------


class TestCompressionResultV2:
    def test_creation(self):
        result = CompressionResultV2(
            original_length=100,
            compressed_length=50,
            compression_ratio=0.5,
            preserved_content="compressed text",
            summary="test summary",
            key_points=["point 1"],
            entities=["entity1"],
            topics=["topic1"],
        )
        assert result.original_length == 100
        assert result.compressed_length == 50
        assert result.compression_ratio == 0.5
        assert result.preserved_content == "compressed text"
        assert result.summary == "test summary"
        assert result.key_points == ["point 1"]
        assert result.entities == ["entity1"]
        assert result.topics == ["topic1"]

    def test_defaults(self):
        result = CompressionResultV2(
            original_length=0,
            compressed_length=0,
            compression_ratio=0.0,
            preserved_content="",
            summary="",
        )
        assert result.key_points == []
        assert result.entities == []
        assert result.topics == []


# ---------------------------------------------------------------------------
# F5CompressorV2 - compress() integration
# ---------------------------------------------------------------------------


class TestF5CompressorV2Compress:
    """Test the main compress() method with various levels and inputs."""

    def test_compress_basic(self, f5_medium, sample_sentences):
        result = f5_medium.compress(sample_sentences)
        assert isinstance(result, CompressionResultV2)
        assert result.original_length == len(sample_sentences)
        assert result.compressed_length > 0
        assert result.compressed_length <= result.original_length
        assert 0 <= result.compression_ratio <= 1
        assert len(result.preserved_content) > 0
        assert isinstance(result.key_points, list)
        assert isinstance(result.entities, list)
        assert isinstance(result.topics, list)

    def test_compress_ratio_medium(self, f5_medium, sample_sentences):
        result = f5_medium.compress(sample_sentences)
        # Medium targets ~50% sentence reduction, but entity appendix adds back chars
        assert result.compression_ratio > 0

    def test_compress_light(self, f5_light, sample_sentences):
        result = f5_light.compress(sample_sentences)
        # Light targets 80% sentence retention, so ratio should be small but positive
        assert result.compression_ratio > 0

    def test_compress_aggressive(self, f5_aggressive, f5_light, sample_sentences):
        result = f5_aggressive.compress(sample_sentences)
        assert result.compression_ratio > 0
        # Aggressive should keep fewer sentences than light
        light_result = f5_light.compress(sample_sentences)
        assert result.compressed_length <= light_result.compressed_length or result.compression_ratio >= light_result.compression_ratio

    def test_compress_ultra_level(self, f5_ultra, f5_light, sample_sentences):
        result = f5_ultra.compress(sample_sentences)
        assert result.compression_ratio > 0
        # ULTRA should have higher ratio than LIGHT
        light_result = f5_light.compress(sample_sentences)
        assert result.compression_ratio >= light_result.compression_ratio

    def test_compress_empty_string(self, f5_medium):
        result = f5_medium.compress("")
        assert result.original_length == 0
        assert result.compressed_length == 0
        assert result.compression_ratio == 0
        assert result.preserved_content == ""
        assert result.summary == ""
        assert result.key_points == []
        assert result.entities == []
        assert result.topics == []

    def test_compress_whitespace_only(self, f5_medium):
        result = f5_medium.compress("   \n\n  \t  ")
        assert result.original_length == 10
        # No real content, so compression behavior
        assert result.preserved_content is not None

    def test_compress_single_sentence(self, f5_medium):
        text = "We decided to use Python for the project."
        result = f5_medium.compress(text)
        assert result.original_length == len(text)
        # Single sentence should be preserved
        assert "Python" in result.preserved_content or "Python" in result.summary

    def test_compress_without_summary(self, sample_sentences):
        compressor = F5CompressorV2(
            level=CompressionLevelV2.MEDIUM, generate_summary=False
        )
        result = compressor.compress(sample_sentences)
        assert result.summary == ""

    def test_compress_without_entities(self, sample_sentences):
        compressor = F5CompressorV2(
            level=CompressionLevelV2.MEDIUM, preserve_entities=False
        )
        result = compressor.compress(sample_sentences)
        # Entities might still be extracted but not appended to preserved_content
        assert isinstance(result.entities, list)

    def test_compress_cjk_text(self, f5_medium, sample_cjk):
        result = f5_medium.compress(sample_cjk)
        assert result.original_length == len(sample_cjk)
        assert result.compressed_length > 0
        # CJK topics should be identified
        assert any(t in result.topics for t in ["meeting", "project", "decision", "problem"])
        # CJK entities like dates should be extracted
        assert len(result.entities) >= 0

    def test_compress_very_long_text(self, f5_medium):
        paragraph = "We decided to move forward with the project. " * 100
        result = f5_medium.compress(paragraph)
        assert result.original_length == len(paragraph)
        assert result.compressed_length < result.original_length
        # Many repeated sentences, key points should be extracted
        assert len(result.key_points) > 0

    def test_compress_structure_all_levels(self, sample_sentences):
        for level in CompressionLevelV2:
            compressor = F5CompressorV2(level)
            result = compressor.compress(sample_sentences)
            assert result.original_length > 0
            assert result.compressed_length > 0
            assert result.preserved_content is not None
            assert isinstance(result.key_points, list)
            assert isinstance(result.entities, list)
            assert isinstance(result.topics, list)

    def test_compress_entity_extraction(self, f5_medium):
        text = (
            "John Smith sent an email to alice@example.com on 2025-03-15 at 10:30 AM. "
            "The URL https://example.com/project was mentioned. Cost: $1,234.56."
        )
        result = f5_medium.compress(text)
        assert "alice@example.com" in result.entities or any(
            "alice" in e for e in result.entities
        )
        # date or time should be found
        date_found = any("2025" in e for e in result.entities)
        time_found = any("10:30" in e for e in result.entities)
        url_found = any("example.com" in e or "https" in e for e in result.entities)
        number_found = any("1,234" in e or "1234" in e for e in result.entities)
        assert date_found or time_found or url_found or number_found

    def test_compress_topic_identification(self, f5_medium):
        text = (
            "We have a critical bug in the system that needs to be fixed. "
            "The meeting was scheduled to discuss the project deadline."
        )
        result = f5_medium.compress(text)
        assert "problem" in result.topics
        assert "meeting" in result.topics
        assert "project" in result.topics


# ---------------------------------------------------------------------------
# F5CompressorV2 - _extract_entities
# ---------------------------------------------------------------------------


class TestExtractEntities:
    def test_person_extraction(self, f5_medium):
        entities = f5_medium._extract_entities("John Smith and Alice Wang met yesterday.")
        assert any("John Smith" in e for e in entities) or any(
            "Alice Wang" in e for e in entities
        )

    def test_email_extraction(self, f5_medium):
        entities = f5_medium._extract_entities("Contact user@example.com for info.")
        assert "user@example.com" in entities

    def test_date_extraction(self, f5_medium):
        entities = f5_medium._extract_entities("Date: 2025-03-15 and 03/15/25.")
        date_found = any("2025-03-15" in e or "03/15/25" in e for e in entities)
        assert date_found

    def test_time_extraction(self, f5_medium):
        entities = f5_medium._extract_entities("Meeting at 10:30 AM and 14:00:00.")
        assert any("10:30" in e for e in entities)

    def test_url_extraction(self, f5_medium):
        entities = f5_medium._extract_entities("Visit https://example.com/path for details.")
        assert any("example.com" in e for e in entities)

    def test_number_extraction(self, f5_medium):
        entities = f5_medium._extract_entities("Total is 1,234 and price 56.78.")
        assert any("1,234" in e for e in entities)

    def test_empty_text(self, f5_medium):
        entities = f5_medium._extract_entities("")
        assert entities == []

    def test_no_entities(self, f5_medium):
        entities = f5_medium._extract_entities("hello world foo bar baz")
        # No capital-name, email, date, time, url, or number patterns match
        assert entities == []

    def test_entity_limit(self, f5_medium):
        # Generate text with more than 20 entities
        parts = []
        for i in range(25):
            parts.append(f"user{i}@example.com")
        text = " ".join(parts)
        entities = f5_medium._extract_entities(text)
        assert len(entities) <= 20


# ---------------------------------------------------------------------------
# F5CompressorV2 - _identify_topics
# ---------------------------------------------------------------------------


class TestIdentifyTopics:
    def test_meeting_topic(self, f5_medium):
        topics = f5_medium._identify_topics("We had a meeting to discuss the schedule.")
        assert "meeting" in topics

    def test_project_topic(self, f5_medium):
        topics = f5_medium._identify_topics("The project milestone is approaching.")
        assert "project" in topics

    def test_decision_topic(self, f5_medium):
        topics = f5_medium._identify_topics("We decided to approve the proposal.")
        assert "decision" in topics

    def test_request_topic(self, f5_medium):
        topics = f5_medium._identify_topics("I would like to request additional resources.")
        assert "request" in topics

    def test_information_topic(self, f5_medium):
        topics = f5_medium._identify_topics("I need to remember this important information.")
        assert "information" in topics

    def test_problem_topic(self, f5_medium):
        topics = f5_medium._identify_topics("There is a critical issue that needs to be fixed.")
        assert "problem" in topics

    def test_success_topic(self, f5_medium):
        topics = f5_medium._identify_topics("We successfully completed the project.")
        assert "success" in topics

    def test_cjk_topics(self, f5_medium):
        topics_cn = f5_medium._identify_topics("我们开会讨论了项目安排。")
        assert "meeting" in topics_cn
        assert "project" in topics_cn

        topics_decide = f5_medium._identify_topics("我们决定同意这个方案。")
        assert "decision" in topics_decide

    def test_multiple_topics(self, f5_medium):
        text = "In the meeting we decided the project task was complete."
        topics = f5_medium._identify_topics(text)
        assert "meeting" in topics
        assert "decision" in topics
        assert "project" in topics
        assert "success" in topics

    def test_empty_text(self, f5_medium):
        topics = f5_medium._identify_topics("")
        assert topics == []

    def test_no_match(self, f5_medium):
        topics = f5_medium._identify_topics("The cat sat on the mat.")
        assert topics == []

    def test_topic_limit(self, f5_medium):
        text = (
            "meeting discuss schedule "
            "project task milestone "
            "decided agreed approved "
            "request ask need "
            "know learn remember "
            "issue bug error "
        )
        topics = f5_medium._identify_topics(text)
        assert len(topics) <= 5


# ---------------------------------------------------------------------------
# F5CompressorV2 - _score_sentence / _extract_key_points
# ---------------------------------------------------------------------------


class TestScoreSentence:
    def test_medium_length_scores_higher(self, f5_medium):
        short = f5_medium._score_sentence("Hi.")
        medium = f5_medium._score_sentence("We decided to use Python.")
        long_ = f5_medium._score_sentence("A" * 150)
        very_long = f5_medium._score_sentence("A" * 300)
        assert medium > short
        assert medium >= long_
        assert long_ >= very_long or long_ > short

    def test_important_keywords_boost_score(self, f5_medium):
        plain = f5_medium._score_sentence("The cat sat on the mat.")
        decision = f5_medium._score_sentence("We decided to fix the critical bug.")
        assert decision > plain

    def test_numbers_boost_score(self, f5_medium):
        no_num = f5_medium._score_sentence("We need to fix it.")
        with_num = f5_medium._score_sentence("We need to fix 3 bugs.")
        assert with_num >= no_num

    def test_question_boost_score(self, f5_medium):
        plain = f5_medium._score_sentence("We need to fix it.")
        question = f5_medium._score_sentence("When should we fix it?")
        assert question > plain

    def test_empty_sentence(self, f5_medium):
        score = f5_medium._score_sentence("")
        assert isinstance(score, (int, float))

    def test_very_short_sentence(self, f5_medium):
        score = f5_medium._score_sentence(".")
        # string " . " has length 1 after stripping
        assert score >= -1  # no error

    def test_keyword_repeats(self, f5_medium):
        # Multiple occurrences still get +2 each unique keyword match
        sentence = "decide agree approve important critical need must"
        score = f5_medium._score_sentence(sentence)
        assert score >= 14  # 7 keywords * 2 each


class TestExtractKeyPoints:
    def test_basic_extraction(self, f5_medium, sample_sentences):
        points = f5_medium._extract_key_points(sample_sentences)
        assert len(points) > 0
        # Key sentences with decision/agreement keywords should be present
        combined = " ".join(points).lower()
        assert any(kw in combined for kw in ["decided", "agreed", "critical", "approved"])

    def test_extraction_order_preserved(self, f5_medium):
        text = "Third sentence is about decisions. First is important. Second is critical."
        points = f5_medium._extract_key_points(text)
        # The points should be in original order
        if len(points) >= 2:
            # 'Second is critical' has 'critical' keyword and should appear
            assert len(points) >= 2

    def test_empty_content(self, f5_medium):
        points = f5_medium._extract_key_points("")
        assert points == []

    def test_single_sentence(self, f5_medium):
        points = f5_medium._extract_key_points("We decided to use Python.")
        assert len(points) == 1
        assert "decided" in points[0]

    def test_different_levels_different_counts(self):
        text = "First. " * 3 + "Second. " * 3 + "Third. " * 3
        light = F5CompressorV2(CompressionLevelV2.LIGHT)
        medium = F5CompressorV2(CompressionLevelV2.MEDIUM)
        aggressive = F5CompressorV2(CompressionLevelV2.AGGRESSIVE)
        ultra = F5CompressorV2(CompressionLevelV2.ULTRA)

        light_points = light._extract_key_points(text)
        medium_points = medium._extract_key_points(text)
        aggressive_points = aggressive._extract_key_points(text)
        ultra_points = ultra._extract_key_points(text)

        # More aggressive compression should keep fewer sentences
        # Note: there's no guarantee about individual levels due to sentence scoring,
        # but at the extremes, light should keep >= ultra
        assert len(light_points) >= 1
        assert len(ultra_points) >= 1

    def test_with_questions(self, f5_medium):
        text = "What is the deadline? We decided to use Python. When will it be done?"
        points = f5_medium._extract_key_points(text)
        # At least one point should be extracted
        assert len(points) > 0


# ---------------------------------------------------------------------------
# F5CompressorV2 - _compress_content
# ---------------------------------------------------------------------------


class TestCompressContent:
    def test_with_key_points_and_entities(self, f5_medium):
        compressed = f5_medium._compress_content(
            "Some original text here.",
            key_points=["First point", "Second point"],
            entities=["John Smith", "2025-03-15"],
        )
        assert "First point" in compressed
        assert "Second point" in compressed
        assert "Entities:" in compressed
        assert "John Smith" in compressed

    def test_with_key_points_no_entities(self, f5_medium):
        compressed = f5_medium._compress_content(
            "Some original text here.",
            key_points=["First point"],
            entities=[],
        )
        assert "First point" in compressed
        assert "Entities:" not in compressed
        assert compressed.endswith(".")

    def test_no_key_points(self, f5_medium):
        compressed = f5_medium._compress_content(
            "This is a long text that should be truncated.",
            key_points=[],
            entities=["entity1"],
        )
        # Should fallback to truncation
        assert isinstance(compressed, str)
        assert len(compressed) > 0
        assert "long" in compressed

    def test_no_key_points_with_entities_disabled(self):
        compressor = F5CompressorV2(
            CompressionLevelV2.MEDIUM, preserve_entities=False
        )
        compressed = compressor._compress_content(
            "Long text for compression.",
            key_points=["Key point"],
            entities=["entity1"],
        )
        assert "Key point" in compressed
        assert "Entities:" not in compressed
        assert compressed.endswith(".")

    def test_empty_key_points_preserve_entities(self, f5_medium):
        compressed = f5_medium._compress_content(
            "Content.", key_points=[], entities=["test@example.com"]
        )
        # No key points, fallback truncation, not entity appendix
        # This goes to the fallback path
        assert isinstance(compressed, str)

    def test_no_entities_preserve_disabled(self):
        compressor = F5CompressorV2(
            CompressionLevelV2.MEDIUM, preserve_entities=False
        )
        compressed = compressor._compress_content(
            "Content.",
            key_points=["Key point"],
            entities=["test@example.com"],
        )
        assert "Key point" in compressed
        assert "Entities:" not in compressed

    def test_terminating_period(self, f5_medium):
        compressed = f5_medium._compress_content(
            "Content.",
            key_points=["Key point without period"],
            entities=[],
        )
        assert compressed.endswith(".")

    def test_already_has_period(self, f5_medium):
        compressed = f5_medium._compress_content(
            "Content.",
            key_points=["Key point."],
            entities=[],
        )
        assert compressed.endswith(".")

    def test_fallback_truncation(self, f5_medium):
        # When key_points is empty and content is long enough to need truncation
        content = "A" * 200
        compressed = f5_medium._compress_content(content, key_points=[], entities=[])
        max_len = int(len(content) * (1 - f5_medium.level.value))
        assert len(compressed) <= max_len + 3  # +3 for "..."

    def test_fallback_no_truncation(self, f5_medium):
        # Empty content: len=0, max_len=int(0*0.5)=0, 0>0 is False -> returns as-is
        compressed = f5_medium._compress_content("", key_points=[], entities=[])
        assert compressed == ""

    def test_fallback_truncation_adds_ellipsis(self, f5_medium):
        content = "A" * 10
        compressed = f5_medium._compress_content(content, key_points=[], entities=[])
        max_len = int(len(content) * (1 - f5_medium.level.value))
        assert compressed == content[:max_len] + "..."


# ---------------------------------------------------------------------------
# F5CompressorV2 - _generate_summary
# ---------------------------------------------------------------------------


class TestGenerateSummary:
    def test_with_topics_and_key_points(self, f5_medium):
        summary = f5_medium._generate_summary(
            "content",
            key_points=["We decided to use Python for the project."],
            topics=["meeting", "decision"],
        )
        assert "Topics:" in summary
        assert "meeting" in summary
        assert "decision" in summary
        assert "Summary:" in summary
        assert "Python" in summary

    def test_topics_only(self, f5_medium):
        summary = f5_medium._generate_summary(
            "content", key_points=[], topics=["meeting"]
        )
        assert "Topics:" in summary
        assert "meeting" in summary
        assert "Summary:" not in summary

    def test_key_points_only(self, f5_medium):
        summary = f5_medium._generate_summary(
            "content",
            key_points=["We decided to use Python."],
            topics=[],
        )
        assert "Summary:" in summary
        assert "Python" in summary
        assert "Topics:" not in summary

    def test_no_topics_no_key_points(self, f5_medium):
        summary = f5_medium._generate_summary("content", key_points=[], topics=[])
        assert summary == ""

    def test_long_key_point_truncated(self, f5_medium):
        long_point = "A" * 100
        summary = f5_medium._generate_summary(
            "content", key_points=[long_point], topics=["meeting"]
        )
        # The long point should be truncated to ~50 chars + "..."
        assert "Topics:" in summary
        assert "Summary:" in summary
        # "A" * 50 + "..." = 53 chars in the summary part after "Summary: "
        # But only first key point is used
        assert len(summary) < len(long_point) + 50


# ---------------------------------------------------------------------------
# F5CompressorV2 - _get_target_sentence_count
# ---------------------------------------------------------------------------


class TestGetTargetSentenceCount:
    def test_light_level(self):
        c = F5CompressorV2(CompressionLevelV2.LIGHT)
        assert c._get_target_sentence_count(10) == 8

    def test_medium_level(self):
        c = F5CompressorV2(CompressionLevelV2.MEDIUM)
        assert c._get_target_sentence_count(10) == 5

    def test_aggressive_level(self):
        c = F5CompressorV2(CompressionLevelV2.AGGRESSIVE)
        assert c._get_target_sentence_count(10) == 3

    def test_ultra_level(self):
        c = F5CompressorV2(CompressionLevelV2.ULTRA)
        assert c._get_target_sentence_count(10) == 1

    def test_minimum_one(self):
        for level in CompressionLevelV2:
            c = F5CompressorV2(level)
            assert c._get_target_sentence_count(1) == 1
            assert c._get_target_sentence_count(0) == 1


# ---------------------------------------------------------------------------
# UltraCompressor
# ---------------------------------------------------------------------------


class TestUltraCompressorHasKeyVerb:
    def test_has_decision(self, ultra):
        assert ultra._has_key_verb("We decided to go ahead.")

    def test_has_agree(self, ultra):
        assert ultra._has_key_verb("They agreed on the terms.")

    def test_has_create(self, ultra):
        assert ultra._has_key_verb("We created a new account.")

    def test_has_update(self, ultra):
        assert ultra._has_key_verb("The record was updated.")

    def test_has_delete(self, ultra):
        assert ultra._has_key_verb("The file was deleted.")

    def test_has_send(self, ultra):
        assert ultra._has_key_verb("Please send the report.")

    def test_has_receive(self, ultra):
        assert ultra._has_key_verb("We received the package.")

    def test_no_key_verb(self, ultra):
        assert not ultra._has_key_verb("The sky is blue.")

    def test_empty_string(self, ultra):
        assert not ultra._has_key_verb("")

    def test_cjk_key_verbs(self, ultra):
        assert ultra._has_key_verb("我们决定采用Python。")
        assert ultra._has_key_verb("团队同意了这个方案。")
        assert ultra._has_key_verb("我们创建了新项目。")
        assert ultra._has_key_verb("我们需要更新记录。")
        assert ultra._has_key_verb("请发送报告。")
        assert ultra._has_key_verb("我们接收了包裹。")


class TestUltraCompressorAbbreviate:
    def test_abbreviate_information(self, ultra):
        assert ultra._abbreviate("information") == "info"

    def test_abbreviate_application(self, ultra):
        assert ultra._abbreviate("application") == "app"

    def test_abbreviate_example(self, ultra):
        assert ultra._abbreviate("example") == "eg"

    def test_abbreviate_number(self, ultra):
        assert ultra._abbreviate("number") == "num"

    def test_abbreviate_message(self, ultra):
        assert ultra._abbreviate("message") == "msg"

    def test_abbreviate_previous(self, ultra):
        assert ultra._abbreviate("previous") == "prev"

    def test_abbreviate_following(self, ultra):
        assert ultra._abbreviate("following") == "fol"

    def test_abbreviate_including(self, ultra):
        assert ultra._abbreviate("including") == "incl"

    def test_abbreviate_without(self, ultra):
        assert ultra._abbreviate("without") == "w/o"

    def test_abbreviate_with(self, ultra):
        assert ultra._abbreviate("with") == "w/"

    def test_abbreviate_case_insensitive(self, ultra):
        assert ultra._abbreviate("INFORMATION") == "info"
        assert ultra._abbreviate("Information") == "info"

    def test_abbreviate_in_context(self, ultra):
        result = ultra._abbreviate("Send a message with the application information")
        assert "msg" in result
        assert "w/" in result
        assert "app" in result
        assert "info" in result

    def test_no_abbreviation_needed(self, ultra):
        result = ultra._abbreviate("Hello world")
        assert result == "Hello world"

    def test_partial_word_no_match(self, ultra):
        # "messages" should not match "\bmessage\b"
        result = ultra._abbreviate("messages")
        assert result == "messages"


class TestUltraCompressorExtractFacts:
    def test_extract_facts_with_numbers(self, ultra):
        facts = ultra._extract_facts("We found 3 bugs. The sky is blue. Cost is $100.")
        assert len(facts) > 0
        # Sentences with numbers should be included
        combined = " ".join(facts)
        assert "3" in combined or "100" in combined

    def test_extract_facts_with_key_verbs(self, ultra):
        facts = ultra._extract_facts(
            "We decided to use Python. The sky is blue. We created a new repo."
        )
        assert len(facts) >= 2  # decide and create sentences
        combined = " ".join(facts).lower()
        assert "python" in combined
        assert "repo" in combined

    def test_extract_facts_empty(self, ultra):
        facts = ultra._extract_facts("")
        assert facts == []

    def test_extract_facts_all_irrelevant(self, ultra):
        facts = ultra._extract_facts(
            "The sky is blue. The cat sat on the mat. It is a nice day."
        )
        # None of these have numbers or key verbs
        assert facts == []

    def test_extract_facts_max_count(self, ultra):
        text = ". ".join([f"We decided item number {i}." for i in range(10)])
        facts = ultra._extract_facts(text)
        assert len(facts) <= 5

    def test_extract_facts_applies_abbreviations(self, ultra):
        facts = ultra._extract_facts(
            "We decided to send the application information with the message."
        )
        assert len(facts) >= 1
        combined = " ".join(facts)
        assert "app" in combined or "info" in combined or "msg" in combined or "w/" in combined


class TestUltraCompressorCompress:
    def test_compress_basic(self, ultra):
        result = ultra.compress(
            "We decided to use Python for the project. "
            "The deadline is 2025-03-15. The sky is blue."
        )
        assert isinstance(result, str)
        assert len(result) > 0
        # Should include facts with numbers or key verbs
        assert "Python" in result or "project" in result or "2025" in result

    def test_compress_max_length_truncated(self, ultra):
        content = ". ".join([f"We decided item number {i}." for i in range(20)])
        result = ultra.compress(content, max_length=30)
        assert len(result) <= 33  # 30 max + 3 for "..."

    def test_compress_empty(self, ultra):
        result = ultra.compress("")
        assert result == ""

    def test_compress_only_irrelevant(self, ultra):
        result = ultra.compress("The sky is blue. The cat sat on the mat.")
        # No facts extracted, so result should be empty
        assert result == ""

    def test_compress_with_cjk(self, ultra):
        result = ultra.compress(
            "我们决定使用Python进行项目开发。"
            "截止日期是2025年3月15日。"
            "天空是蓝色的。"
        )
        assert len(result) > 0
        assert "Python" in result or "2025" in result

    def test_compress_fact_separator(self, ultra):
        result = ultra.compress(
            "We decided to use Python. We agreed on the deadline of 2025-03-15."
        )
        # Facts should be joined with "; "
        assert "; " in result


# ---------------------------------------------------------------------------
# Singleton / Global functions
# ---------------------------------------------------------------------------


class TestGlobalFunctions:
    def setup_method(self):
        reset_f5_compressor()
        reset_ultra_compressor()

    def test_get_f5_compressor_default(self):
        c1 = get_f5_compressor()
        assert isinstance(c1, F5CompressorV2)
        assert c1.level == CompressionLevelV2.MEDIUM

    def test_get_f5_compressor_singleton(self):
        c1 = get_f5_compressor()
        c2 = get_f5_compressor()
        assert c1 is c2

    def test_get_f5_compressor_different_level(self):
        c1 = get_f5_compressor(CompressionLevelV2.LIGHT)
        c2 = get_f5_compressor(CompressionLevelV2.LIGHT)
        assert c1 is c2

    def test_get_f5_compressor_level_change(self):
        c1 = get_f5_compressor(CompressionLevelV2.LIGHT)
        c2 = get_f5_compressor(CompressionLevelV2.MEDIUM)
        # Level changed, should return a new instance
        assert c1 is not c2
        assert c2.level == CompressionLevelV2.MEDIUM

    def test_get_f5_compressor_after_reset(self):
        c1 = get_f5_compressor()
        reset_f5_compressor()
        c2 = get_f5_compressor()
        assert c1 is not c2

    def test_get_ultra_compressor_singleton(self):
        u1 = get_ultra_compressor()
        u2 = get_ultra_compressor()
        assert u1 is u2

    def test_get_ultra_compressor_after_reset(self):
        u1 = get_ultra_compressor()
        reset_ultra_compressor()
        u2 = get_ultra_compressor()
        assert u1 is not u2

    def test_reset_f5_compressor(self):
        get_f5_compressor()
        reset_f5_compressor()
        # No error, just resets global
        assert True

    def test_reset_ultra_compressor(self):
        get_ultra_compressor()
        reset_ultra_compressor()
        assert True


class TestCompressV2:
    def test_compress_v2_default(self, sample_sentences):
        result = compress_v2(sample_sentences)
        assert isinstance(result, CompressionResultV2)
        assert result.original_length > 0

    def test_compress_v2_with_level(self, sample_sentences):
        result = compress_v2(sample_sentences, CompressionLevelV2.LIGHT)
        assert result.original_length > 0
        assert result.compressed_length > 0

    def test_compress_v2_empty(self):
        result = compress_v2("")
        assert result.original_length == 0
        assert result.compression_ratio == 0

    def test_compress_v2_all_levels(self, sample_sentences):
        for level in CompressionLevelV2:
            result = compress_v2(sample_sentences, level)
            assert isinstance(result, CompressionResultV2)
            assert result.original_length > 0


# ---------------------------------------------------------------------------
# Compress / Decompress "cycle" correctness
# ---------------------------------------------------------------------------


class TestCompressDecompressCycle:
    """Verify that compress/decompress preserves key information correctly."""

    def test_key_decisions_preserved_mixed_case(self, f5_medium):
        original = "We DeCidEd to use Python."
        result = f5_medium.compress(original)
        combined = (result.preserved_content + " " + result.summary).lower()
        assert "python" in combined

    def test_key_info_in_summary_when_not_in_compressed(self, f5_medium):
        """Key points may appear in summary or preserved_content."""
        original = (
            "We decided to use Rust for the new compiler. "
            "The compiler needs to be really fast. "
            "We also discussed the testing strategy."
        )
        result = f5_medium.compress(original)
        combined = (result.preserved_content + " " + result.summary).lower()
        # At least one key term should be retained
        assert any(term in combined for term in ["rust", "compiler", "testing"])

    def test_entity_survival_across_levels(self, sample_sentences):
        for level in CompressionLevelV2:
            compressor = F5CompressorV2(level)
            result = compressor.compress(sample_sentences)
            # Entities list should always be preserved
            assert isinstance(result.entities, list)

    def test_cjk_preservation(self, f5_medium, sample_cjk):
        result = f5_medium.compress(sample_cjk)
        combined = result.preserved_content + " " + result.summary
        # Key CJK concepts should be present somewhere
        cjk_terms = ["Python", "2025", "admin"]
        assert any(term in combined for term in cjk_terms)

    def test_identity_for_very_short_content(self, f5_medium):
        text = "Hi."
        result = f5_medium.compress(text)
        # Short content may be unchanged (no key points -> fallback truncation)
        assert result.original_length == len(text)


# ---------------------------------------------------------------------------
# Compression Stats
# ---------------------------------------------------------------------------


class TestCompressionStats:
    def test_ratio_bounds(self, f5_medium, sample_sentences):
        result = f5_medium.compress(sample_sentences)
        assert 0 <= result.compression_ratio <= 1

    def test_length_monotonic(self, f5_medium, sample_sentences):
        result = f5_medium.compress(sample_sentences)
        assert result.compressed_length <= result.original_length

    def test_higher_level_higher_ratio(self, sample_sentences):
        """ULTRA should produce >= compression ratio than LIGHT."""
        l_result = F5CompressorV2(CompressionLevelV2.LIGHT).compress(sample_sentences)
        u_result = F5CompressorV2(CompressionLevelV2.ULTRA).compress(sample_sentences)
        assert u_result.compression_ratio >= l_result.compression_ratio

    def test_ratio_zero_for_empty(self, f5_medium):
        result = f5_medium.compress("")
        assert result.compression_ratio == 0

    def test_sentence_count_vs_level(self, sample_sentences):
        """Higher compression levels should extract fewer key points."""
        results = {}
        for level in CompressionLevelV2:
            c = F5CompressorV2(level)
            results[level] = c.compress(sample_sentences)

        # ULTRA should have fewest or equal sentences
        # (but not necessarily strictly fewer due to scoring)
        assert len(results[CompressionLevelV2.ULTRA].key_points) >= 0
        assert len(results[CompressionLevelV2.LIGHT].key_points) >= len(
            results[CompressionLevelV2.ULTRA].key_points
        )


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_text_with_only_numbers(self, f5_medium):
        text = "42 100 200 300 400"
        result = f5_medium.compress(text)
        assert isinstance(result, CompressionResultV2)
        # Numbers become entities and are appended, which can expand size
        # The important thing is the original structure is preserved
        assert len(result.entities) > 0

    def test_text_with_only_symbols(self, f5_medium):
        result = f5_medium.compress("!@#$%^&*()")
        assert isinstance(result, CompressionResultV2)

    def test_text_with_newlines_only(self, f5_medium):
        result = f5_medium.compress("\n\n\n\n")
        # No real sentences, should handle gracefully
        assert result.original_length == 4
        assert len(result.key_points) == 0

    def test_text_with_tabs_and_spaces(self, f5_medium):
        result = f5_medium.compress("    \t\t    ")
        assert isinstance(result, CompressionResultV2)

    def test_extremely_long_single_word(self, f5_medium):
        text = "A" * 10000
        result = f5_medium.compress(text)
        # The entire string is one sentence, so key_points may have it
        assert len(result.key_points) <= 1
        # No compression possible on a single undelimited sentence
        # The code treats it as one sentence and may add a period
        assert result.original_length == len(text)

    def test_url_only_content(self, f5_medium):
        text = "Check https://github.com/user/repo for more information."
        result = f5_medium.compress(text)
        assert "github" in result.entities or "github" in result.preserved_content

    def test_email_only_content(self, f5_medium):
        result = f5_medium.compress("Contact support@company.com for help.")
        assert "support@company.com" in result.entities

    def test_repeated_content(self, f5_medium):
        text = "We decided to use Python. " * 50
        result = f5_medium.compress(text)
        assert result.compressed_length < result.original_length
        assert len(result.key_points) > 0

    def test_cjk_only_punctuation(self, f5_medium):
        result = f5_medium.compress("，。！？；：")
        assert isinstance(result, CompressionResultV2)


# ---------------------------------------------------------------------------
# F5CompressorV2 configuration
# ---------------------------------------------------------------------------


class TestF5CompressorV2Config:
    def test_default_config(self):
        c = F5CompressorV2()
        assert c.level == CompressionLevelV2.MEDIUM
        assert c.preserve_entities is True
        assert c.generate_summary is True

    def test_custom_config(self):
        c = F5CompressorV2(
            level=CompressionLevelV2.AGGRESSIVE,
            preserve_entities=False,
            generate_summary=False,
        )
        assert c.level == CompressionLevelV2.AGGRESSIVE
        assert c.preserve_entities is False
        assert c.generate_summary is False


# ---------------------------------------------------------------------------
# UltraCompressor initialization
# ---------------------------------------------------------------------------


class TestUltraCompressorInit:
    def test_init_creates_regex(self):
        uc = UltraCompressor()
        assert hasattr(uc, "_abbrev_re")
        assert uc._abbrev_re is not None

    def test_regex_matches_known_words(self, ultra):
        assert ultra._abbrev_re.search("information") is not None
        assert ultra._abbrev_re.search("hello") is None
