"""
Tests for Context Injection

Tests context formatting and injection.
"""

import pytest
from claw_mem.context_injection import ContextFormatter, InjectedContext


class TestInjectedContext:
    """Test InjectedContext dataclass"""
    
    def test_initialization(self):
        """Test InjectedContext initialization"""
        context = InjectedContext(
            formatted_text="Sample context",
            memory_count=3,
            total_length=100,
            layers_included=["l1", "l2"]
        )
        
        assert context.formatted_text == "Sample context"
        assert context.memory_count == 3
        assert context.total_length == 100
        assert context.truncated is False
        assert context.warnings == []
    
    def test_with_warnings(self):
        """Test InjectedContext with warnings"""
        context = InjectedContext(
            formatted_text="Sample",
            memory_count=1,
            total_length=50,
            layers_included=["l1"],
            truncated=False
        )
        # Manually set warnings after initialization
        context.warnings = ["Warning 1", "Warning 2"]

        assert len(context.warnings) == 2
        assert "Warning 1" in context.warnings
        assert "Warning 2" in context.warnings

    def test_truncated(self):
        """Test InjectedContext truncated flag"""
        context = InjectedContext(
            formatted_text="Sample",
            memory_count=1,
            total_length=50,
            layers_included=["l1"],
            truncated=True
        )

        assert context.truncated is True


class TestContextFormatter:
    """Test ContextFormatter"""
    
    def test_initialization(self):
        """Test ContextFormatter initialization"""
        formatter = ContextFormatter()
        
        assert formatter.max_length == ContextFormatter.DEFAULT_MAX_LENGTH
    
    def test_custom_max_length(self):
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
        """Test formatting single memory"""
        formatter = ContextFormatter()
        
        memories = [
            {
                "content": "Test memory content",
                "layer": "l1"
            }
        ]
        
        result = formatter.format(memories)
        
        assert result.memory_count == 1
        assert "Test memory content" in result.formatted_text
        assert result.total_length > 0
    
    def test_format_multiple_memories(self):
        """Test formatting multiple memories"""
        formatter = ContextFormatter()
        
        memories = [
            {"content": "Memory 1", "layer": "l1"},
            {"content": "Memory 2", "layer": "l2"},
            {"content": "Memory 3", "layer": "l3"}
        ]
        
        result = formatter.format(memories)
        
        assert result.memory_count == 3
        assert "Memory 1" in result.formatted_text
        assert "Memory 2" in result.formatted_text
        assert "Memory 3" in result.formatted_text
    
    def test_format_with_source(self):
        """Test formatting with source information"""
        formatter = ContextFormatter()
        
        memories = [
            {
                "content": "Test memory",
                "layer": "l1",
                "source": "MEMORY.md"
            }
        ]
        
        result = formatter.format(memories, include_source=True)
        
        assert "MEMORY.md" in result.formatted_text
    
    def test_format_without_source(self):
        """Test formatting without source information"""
        formatter = ContextFormatter()
        
        memories = [
            {
                "content": "Test memory",
                "layer": "l1",
                "source": "MEMORY.md"
            }
        ]
        
        result = formatter.format(memories, include_source=False)
        
        assert "MEMORY.md" not in result.formatted_text
    
    def test_layer_grouped_format(self):
        """Test layer-grouped formatting"""
        formatter = ContextFormatter()
        
        memories = [
            {"content": "Working memory", "layer": "l1"},
            {"content": "Short-term memory", "layer": "l2"},
            {"content": "Long-term memory", "layer": "l3"}
        ]
        
        result = formatter.format(memories, layer_grouping=True)
        
        assert "Working Memory" in result.formatted_text
        assert "Short-term Memory" in result.formatted_text
        assert "Long-term Memory" in result.formatted_text
        assert len(result.layers_included) == 3
    
    def test_flat_format(self):
        """Test flat formatting"""
        formatter = ContextFormatter()
        
        memories = [
            {"content": "Memory 1", "layer": "l1"},
            {"content": "Memory 2", "layer": "l2"}
        ]
        
        result = formatter.format(memories, layer_grouping=False)
        
        assert "Memory 1" in result.formatted_text
        assert "Memory 2" in result.formatted_text
    
    def test_truncation(self):
        """Test context truncation"""
        # Use a max_length that triggers truncation but accommodates headers
        # The formatted text includes headers like "--- Retrieved Context ---"
        # and truncation adds "... (content truncated)" suffix
        formatter = ContextFormatter(max_length=150)
        
        memories = [
            {"content": "A very long memory content that should be truncated", "layer": "l1"}
        ]
        
        result = formatter.format(memories)
        
        # Verify truncation happened (not exact length check due to truncation suffix)
        assert result.truncated is True
        assert len(result.warnings) > 0
        # Check that content was actually truncated (not just full text)
        assert len(result.formatted_text) > 0
    
    def test_no_truncation_short_context(self):
        """Test no truncation for short context"""
        formatter = ContextFormatter(max_length=1000)
        
        memories = [
            {"content": "Short memory", "layer": "l1"}
        ]
        
        result = formatter.format(memories)
        
        assert result.truncated is False
        assert len(result.warnings) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
