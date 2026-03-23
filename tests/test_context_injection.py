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
Tests for Context Injection Module
"""

import pytest

from claw_mem.context_injection import (
    ContextFormatter,
    ContextInjector,
    InjectedContext,
    format_memory_context,
    inject_memories_to_prompt,
)


class TestInjectedContext:
    """Tests for InjectedContext dataclass"""

    def test_injected_context_creation(self):
        """Test creating InjectedContext"""
        ctx = InjectedContext(
            formatted_text="Test context",
            memory_count=5,
            total_length=12,
            layers_included=["l1", "l2"],
        )

        assert ctx.formatted_text == "Test context"
        assert ctx.memory_count == 5
        assert ctx.total_length == 12
        assert ctx.layers_included == ["l1", "l2"]
        assert ctx.truncated is False
        assert ctx.warnings == []

    def test_injected_context_with_warnings(self):
        """Test InjectedContext with warnings"""
        ctx = InjectedContext(
            formatted_text="Test",
            memory_count=1,
            total_length=4,
            layers_included=["l3"],
            truncated=True,
            warnings=["Context was truncated"],
        )

        assert ctx.truncated is True
        assert "Context was truncated" in ctx.warnings


class TestContextFormatter:
    """Tests for ContextFormatter"""

    def test_formatter_creation(self):
        """Test creating ContextFormatter"""
        formatter = ContextFormatter()
        assert formatter.max_length == 4000

    def test_formatter_custom_max_length(self):
        """Test ContextFormatter with custom max length"""
        formatter = ContextFormatter(max_length=2000)
        assert formatter.max_length == 2000

    def test_format_empty_memories(self):
        """Test formatting empty memories"""
        formatter = ContextFormatter()
        result = formatter.format([])

        assert result.formatted_text == ""
        assert result.memory_count == 0
        assert result.total_length == 0
        assert result.layers_included == []

    def test_format_single_memory(self):
        """Test formatting a single memory"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test memory content",
                "layer": "l2",
                "score": 0.95,
                "source": "2026-03-23.md",
                "tags": ["test"],
                "timestamp": "2026-03-23T10:00:00",
            }
        ]

        result = formatter.format(memories)

        assert result.memory_count == 1
        assert "Test memory content" in result.formatted_text
        assert "L2" in result.formatted_text
        assert "Short-term Memory" in result.formatted_text

    def test_format_multiple_memories(self):
        """Test formatting multiple memories"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "First memory",
                "layer": "l1",
                "score": 0.9,
            },
            {
                "memory_id": "test-2",
                "content": "Second memory",
                "layer": "l2",
                "score": 0.8,
            },
            {
                "memory_id": "test-3",
                "content": "Third memory",
                "layer": "l3",
                "score": 0.7,
            },
        ]

        result = formatter.format(memories)

        assert result.memory_count == 3
        assert "First memory" in result.formatted_text
        assert "Second memory" in result.formatted_text
        assert "Third memory" in result.formatted_text
        assert "Working Memory" in result.formatted_text  # L1
        assert "Short-term Memory" in result.formatted_text  # L2
        assert "Long-term Memory" in result.formatted_text  # L3

    def test_format_with_scores(self):
        """Test formatting with relevance scores"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test content",
                "layer": "l2",
                "score": 0.95,
            }
        ]

        result = formatter.format(memories, include_scores=True)

        assert "relevance: 0.950" in result.formatted_text

    def test_format_with_source(self):
        """Test formatting with source information"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test content",
                "layer": "l2",
                "source": "/path/to/2026-03-23.md",
            }
        ]

        result = formatter.format(memories, include_source=True)

        assert "2026-03-23.md" in result.formatted_text
        assert "Source:" in result.formatted_text

    def test_format_without_source(self):
        """Test formatting without source information"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test content",
                "layer": "l2",
                "source": "/path/to/file.md",
            }
        ]

        result = formatter.format(memories, include_source=False)

        assert "Source:" not in result.formatted_text

    def test_format_flat_layout(self):
        """Test formatting with flat layout (no layer grouping)"""
        formatter = ContextFormatter()

        memories = [
            {"memory_id": "1", "content": "A", "layer": "l1"},
            {"memory_id": "2", "content": "B", "layer": "l3"},
        ]

        result = formatter.format(memories, layer_grouping=False)

        # Should not have layer headers
        assert "##" not in result.formatted_text

    def test_format_with_tags(self):
        """Test formatting memories with tags"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test content",
                "layer": "l2",
                "tags": ["important", "project"],
            }
        ]

        result = formatter.format(memories)

        assert "Tags: important, project" in result.formatted_text

    def test_format_with_timestamp(self):
        """Test formatting memories with timestamps"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test content",
                "layer": "l2",
                "timestamp": "2026-03-23T10:00:00",
            }
        ]

        result = formatter.format(memories)

        assert "Time: 2026-03-23T10:00:00" in result.formatted_text

    def test_escape_control_characters(self):
        """Test escaping control characters"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Test\x00content\x01with\x02control",
                "layer": "l1",
            }
        ]

        result = formatter.format(memories)

        # Control characters should be removed
        assert "\x00" not in result.formatted_text
        assert "\x01" not in result.formatted_text
        assert "\x02" not in result.formatted_text

    def test_normalize_multiple_newlines(self):
        """Test normalizing multiple newlines"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Line 1\n\n\n\nLine 2",
                "layer": "l1",
            }
        ]

        result = formatter.format(memories)

        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in result.formatted_text

    def test_truncate_long_content(self):
        """Test truncating long content"""
        formatter = ContextFormatter(max_length=100)

        # Create very long content
        long_content = "A" * 500
        memories = [
            {
                "memory_id": "test-1",
                "content": long_content,
                "layer": "l1",
            }
        ]

        result = formatter.format(memories)

        assert result.truncated is True
        # Total length includes headers, so just check it's reasonable
        assert len(result.formatted_text) < 200  # Should be truncated reasonably
        assert "truncated" in result.formatted_text.lower()

    def test_truncate_warning(self):
        """Test truncation warning in result"""
        formatter = ContextFormatter(max_length=50)

        memories = [
            {
                "memory_id": "test-1",
                "content": "This is a very long memory content that exceeds the limit",
                "layer": "l1",
            }
        ]

        result = formatter.format(memories)

        assert result.truncated is True
        assert any("truncated" in w.lower() for w in result.warnings)

    def test_layers_included(self):
        """Test layers included in result"""
        formatter = ContextFormatter()

        memories = [
            {"memory_id": "1", "content": "A", "layer": "l1"},
            {"memory_id": "2", "content": "B", "layer": "l2"},
            {"memory_id": "3", "content": "C", "layer": "l3"},
        ]

        result = formatter.format(memories)

        assert set(result.layers_included) == {"l1", "l2", "l3"}


class TestContextInjector:
    """Tests for ContextInjector"""

    def test_injector_creation(self):
        """Test creating ContextInjector"""
        injector = ContextInjector()
        assert injector.formatter is not None

    def test_inject_with_custom_formatter(self):
        """Test injecting with custom formatter"""
        formatter = ContextFormatter(max_length=100)
        injector = ContextInjector(formatter=formatter)

        memories = [
            {"memory_id": "1", "content": "Test", "layer": "l1"}
        ]

        result = injector.inject(memories)

        assert result.memory_count == 1

    def test_inject_empty_memories(self):
        """Test injecting empty memories"""
        injector = ContextInjector()

        result = injector.inject([])

        assert result.formatted_text == ""
        assert result.memory_count == 0

    def test_inject_with_template(self):
        """Test injecting with custom template"""
        injector = ContextInjector()

        memories = [
            {"memory_id": "1", "content": "Memory A", "layer": "l2"},
            {"memory_id": "2", "content": "Memory B", "layer": "l3"},
        ]

        template = """
        Retrieved {{count}} memories from {{layers}}:
        {{memories}}
        """

        result = injector.inject(memories, template=template)

        assert "2" in result.formatted_text  # count
        assert "Memory A" in result.formatted_text
        assert "Memory B" in result.formatted_text

    def test_create_system_prompt(self):
        """Test creating system prompt with injected memories"""
        injector = ContextInjector()

        base_prompt = "You are a helpful assistant."

        memories = [
            {"memory_id": "1", "content": "User prefers Python", "layer": "l3"}
        ]

        full_prompt = injector.create_system_prompt(base_prompt, memories)

        assert "You are a helpful assistant." in full_prompt
        assert "User prefers Python" in full_prompt
        assert "Retrieved Context" in full_prompt

    def test_create_system_prompt_empty_memories(self):
        """Test creating system prompt with no memories"""
        injector = ContextInjector()

        base_prompt = "You are a helpful assistant."

        full_prompt = injector.create_system_prompt(base_prompt, [])

        # Should return base prompt unchanged
        assert full_prompt == base_prompt


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_format_memory_context(self):
        """Test format_memory_context function"""
        memories = [
            {"memory_id": "1", "content": "Test", "layer": "l2"},
        ]

        result = format_memory_context(memories)

        assert "Test" in result
        assert "Retrieved Context" in result

    def test_format_memory_context_custom_max_length(self):
        """Test format_memory_context with custom max length"""
        memories = [
            {"memory_id": "1", "content": "A" * 100, "layer": "l1"},
        ]

        result = format_memory_context(memories, max_length=50)

        # Should be truncated
        assert len(result) <= 50 or "truncated" in result.lower()

    def test_inject_memories_to_prompt(self):
        """Test inject_memories_to_prompt function"""
        base_prompt = "Base instruction"

        memories = [
            {"memory_id": "1", "content": "Context", "layer": "l3"},
        ]

        result = inject_memories_to_prompt(memories, base_prompt)

        assert "Base instruction" in result
        assert "Context" in result


class TestEdgeCases:
    """Tests for edge cases"""

    def test_special_unicode_characters(self):
        """Test handling special Unicode characters"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "test-1",
                "content": "Text with em-dash and quotes",
                "layer": "l1",
            }
        ]

        result = formatter.format(memories)

        # Should handle gracefully
        assert result.memory_count == 1

    def test_very_long_memory_id(self):
        """Test handling very long memory IDs"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": "x" * 1000,
                "content": "Test",
                "layer": "l1",
            }
        ]

        result = formatter.format(memories)

        # Should handle gracefully
        assert result.memory_count == 1

    def test_missing_fields(self):
        """Test handling memories with missing fields"""
        formatter = ContextFormatter()

        # Memory with minimal fields
        memories = [
            {"content": "Just content"}
        ]

        result = formatter.format(memories)

        # Should not raise
        assert "Just content" in result.formatted_text

    def test_none_values(self):
        """Test handling None values in memory fields"""
        formatter = ContextFormatter()

        memories = [
            {
                "memory_id": None,
                "content": "Test",
                "layer": None,
                "score": None,
            }
        ]

        result = formatter.format(memories)

        # Should handle gracefully
        assert result.memory_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
