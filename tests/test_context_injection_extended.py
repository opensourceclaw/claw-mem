"""
Extended tests for Context Injection

Tests additional coverage for context formatting and injection.
"""

import pytest
from claw_mem.context_injection import (
    ContextFormatter,
    InjectedContext,
    ContextInjector,
    format_memory_context,
    inject_memories_to_prompt
)


class TestContextFormatterExtended:
    """Extended tests for ContextFormatter"""

    def test_format_with_scores(self):
        """Test formatting with relevance scores"""
        formatter = ContextFormatter()

        memories = [
            {
                "content": "High relevance memory",
                "layer": "l1",
                "score": 0.95
            },
            {
                "content": "Low relevance memory",
                "layer": "l2",
                "score": 0.45
            }
        ]

        result = formatter.format(memories, include_scores=True)

        assert "(relevance: 0.950)" in result.formatted_text
        assert "(relevance: 0.450)" in result.formatted_text
        assert result.memory_count == 2

    def test_format_with_memory_result_object(self):
        """Test formatting with custom memory result objects"""
        # Create a mock MemoryResult object with hasattr support
        class MockMemoryResult:
            def __init__(self, content, layer, memory_id=None, score=None, tags=None):
                self.content = content
                self.layer = layer
                self.memory_id = memory_id
                self.score = score
                self.tags = tags or []
                self.timestamp = "2026-04-11T10:00:00"

        formatter = ContextFormatter()

        # Create MockMemoryResult objects
        memory1 = MockMemoryResult(
            content="Test memory",
            layer="l1",
            memory_id="test-1",
            score=0.8,
            tags=["test"]
        )

        result = formatter.format([memory1])

        assert result.memory_count == 1
        assert "Test memory" in result.formatted_text

    def test_escape_content_special_chars(self):
        """Test escaping of special characters"""
        formatter = ContextFormatter()

        content = "Text\x00with\x07control\x1fcharacters\nand\n\n\nnewlines"
        memories = [{"content": content, "layer": "l1"}]

        result = formatter.format(memories)

        # Control characters should be removed
        assert "\x00" not in result.formatted_text
        assert "\x07" not in result.formatted_text
        assert "\x1f" not in result.formatted_text

        # Multiple newlines normalized to double newline
        assert "\n\n\n" not in result.formatted_text
        assert "\n\n" in result.formatted_text

    def test_escape_content_long_entry(self):
        """Test truncation of very long individual entries"""
        formatter = ContextFormatter()

        long_content = "A" * 1500  # Exceeds 1000 char limit
        memories = [{"content": long_content, "layer": "l1"}]

        result = formatter.format(memories)

        # Should be truncated with ellipsis
        assert len(result.formatted_text) < len(long_content)
        assert "..." in result.formatted_text

    def test_truncate_at_section_boundary(self):
        """Test truncation at section boundary"""
        formatter = ContextFormatter(max_length=100)

        memories = [
            {"content": "Short", "layer": "l1"},
            {"content": "Medium length content here", "layer": "l2"}
        ]

        result = formatter.format(memories)

        assert result.truncated is True
        assert len(result.warnings) > 0
        assert "truncated" in result.warnings[0].lower()

    def test_format_with_metadata(self):
        """Test formatting with memory metadata"""
        formatter = ContextFormatter()

        memories = [
            {
                "content": "Test memory",
                "layer": "l1",
                "memory_id": "mem-123",
                "source": "/path/to/MEMORY.md",
                "tags": ["important", "test"],
                "timestamp": "2026-04-11T10:00:00"
            }
        ]

        result = formatter.format(memories, include_source=True)

        assert "Source: MEMORY.md" in result.formatted_text
        assert "Tags: important, test" in result.formatted_text
        assert "Time: 2026-04-11" in result.formatted_text

    def test_format_without_working_memory_source(self):
        """Test that working_memory source is not displayed"""
        formatter = ContextFormatter()

        memories = [
            {
                "content": "Working memory",
                "layer": "l1",
                "source": "working_memory"
            }
        ]

        result = formatter.format(memories, include_source=True)

        assert "working_memory" not in result.formatted_text

    def test_format_with_tags(self):
        """Test formatting with tags"""
        formatter = ContextFormatter()

        memories = [
            {
                "content": "Test",
                "layer": "l1",
                "tags": ["tag1", "tag2", "tag3"]
            }
        ]

        result = formatter.format(memories)

        assert "Tags: tag1, tag2, tag3" in result.formatted_text

    def test_format_empty_tags(self):
        """Test formatting with empty tags list"""
        formatter = ContextFormatter()

        memories = [
            {
                "content": "Test",
                "layer": "l1",
                "tags": []
            }
        ]

        result = formatter.format(memories)

        # Should not display tags metadata
        assert "Tags:" not in result.formatted_text

    def test_unknown_layer(self):
        """Test formatting with unknown layer"""
        formatter = ContextFormatter()

        memories = [
            {"content": "Test", "layer": "unknown_layer"}
        ]

        result = formatter.format(memories)

        assert "Test" in result.formatted_text
        assert "UNKNOWN_LAYER" in result.formatted_text

    def test_flat_format_with_multiple_layers(self):
        """Test flat format with memories from different layers"""
        formatter = ContextFormatter()

        memories = [
            {"content": "Memory 1", "layer": "l1"},
            {"content": "Memory 2", "layer": "l2"},
            {"content": "Memory 3", "layer": "l3"}
        ]

        result = formatter.format(memories, layer_grouping=False)

        assert "Memory 1" in result.formatted_text
        assert "Memory 2" in result.formatted_text
        assert "Memory 3" in result.formatted_text
        # Should NOT have layer section headers in flat mode
        assert "Working Memory" not in result.formatted_text


class TestContextInjector:
    """Test ContextInjector"""

    def test_inject_default_formatter(self):
        """Test injection with default formatter"""
        injector = ContextInjector()

        memories = [
            {"content": "Test", "layer": "l1"}
        ]

        result = injector.inject(memories)

        assert result.memory_count == 1
        assert "Test" in result.formatted_text

    def test_inject_custom_formatter(self):
        """Test injection with custom formatter"""
        custom_formatter = ContextFormatter(max_length=100)
        injector = ContextInjector(formatter=custom_formatter)

        memories = [
            {"content": "Test", "layer": "l1"}
        ]

        result = injector.inject(memories)

        assert result.memory_count == 1

    def test_inject_with_template(self):
        """Test injection with custom template"""
        injector = ContextInjector()

        memories = [
            {"content": "Memory 1", "layer": "l1"},
            {"content": "Memory 2", "layer": "l2"}
        ]

        template = "Context:\n{{memories}}\nTotal: {{count}}\nLayers: {{layers}}"

        result = injector.inject(memories, template=template)

        assert "Context:" in result.formatted_text
        assert "Total: 2" in result.formatted_text
        assert "Layers:" in result.formatted_text

    def test_create_system_prompt_with_context(self):
        """Test creating system prompt with injected context"""
        injector = ContextInjector()

        base_prompt = "You are a helpful assistant."
        memories = [
            {"content": "User likes pizza", "layer": "l1"}
        ]

        full_prompt = injector.create_system_prompt(base_prompt, memories)

        assert base_prompt in full_prompt
        assert "User likes pizza" in full_prompt
        assert len(full_prompt) > len(base_prompt)

    def test_create_system_prompt_without_context(self):
        """Test creating system prompt without context"""
        injector = ContextInjector()

        base_prompt = "You are a helpful assistant."
        full_prompt = injector.create_system_prompt(base_prompt, [])

        # Should just return base prompt unchanged
        assert full_prompt == base_prompt


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_format_memory_context(self):
        """Test format_memory_context convenience function"""
        memories = [
            {"content": "Test", "layer": "l1"}
        ]

        result = format_memory_context(memories, max_length=1000, group_by_layer=True)

        assert isinstance(result, str)
        assert "Test" in result

    def test_format_memory_context_flat(self):
        """Test format_memory_context with flat format"""
        memories = [
            {"content": "Test", "layer": "l1"}
        ]

        result = format_memory_context(memories, group_by_layer=False)

        assert isinstance(result, str)
        assert "Test" in result

    def test_inject_memories_to_prompt(self):
        """Test inject_memories_to_prompt convenience function"""
        base_prompt = "Base prompt"
        memories = [
            {"content": "Memory content", "layer": "l1"}
        ]

        result = inject_memories_to_prompt(memories, base_prompt)

        assert base_prompt in result
        assert "Memory content" in result


class TestEdgeCases:
    """Test edge cases"""

    def test_format_with_none_layer(self):
        """Test formatting with None layer"""
        formatter = ContextFormatter()

        memories = [
            {"content": "Test", "layer": None}
        ]

        result = formatter.format(memories)

        assert "Test" in result.formatted_text
        # Should use "UNKNOWN" as fallback
        assert "UNKNOWN" in result.formatted_text

    def test_format_with_missing_content(self):
        """Test formatting with missing content"""
        formatter = ContextFormatter()

        memories = [
            {"layer": "l1"}  # No content
        ]

        result = formatter.format(memories)

        # Should handle gracefully
        assert result.memory_count == 1

    def test_truncate_exact_length(self):
        """Test truncation when text is exactly at max length"""
        formatter = ContextFormatter(max_length=100)

        # Create text that will be exactly at max after formatting
        memories = [
            {"content": "Short", "layer": "l1"}
        ]

        result = formatter.format(memories)

        # Should not truncate if at or below max length
        if len(result.formatted_text) <= 100:
            assert result.truncated is False
            assert len(result.warnings) == 0

    def test_format_with_zero_score(self):
        """Test formatting with zero relevance score"""
        formatter = ContextFormatter()

        memories = [
            {"content": "Test", "layer": "l1", "score": 0.0}
        ]

        result = formatter.format(memories, include_scores=True)

        assert "(relevance: 0.000)" in result.formatted_text

    def test_format_with_negative_score(self):
        """Test formatting with negative relevance score"""
        formatter = ContextFormatter()

        memories = [
            {"content": "Test", "layer": "l1", "score": -0.5}
        ]

        result = formatter.format(memories, include_scores=True)

        assert "(relevance: -0.500)" in result.formatted_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
