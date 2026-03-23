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
Context Injection Module

Handles formatting and injection of retrieved memories into session prompts.

Features:
- Proper formatting of retrieved memories
- Edge case handling (empty results, special characters)
- Context length management
- Layer-aware formatting
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class InjectedContext:
    """Result of context injection"""
    formatted_text: str
    memory_count: int
    total_length: int
    layers_included: List[str]
    truncated: bool = False
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ContextFormatter:
    """
    Formats retrieved memories for prompt injection

    Handles:
    - Empty results
    - Special character escaping
    - Layer-aware formatting
    - Context length limits
    """

    # Default context length limit (tokens approximated as characters/4)
    DEFAULT_MAX_LENGTH = 4000  # ~1000 tokens

    # Layer display names
    LAYER_NAMES = {
        "l1": "Working Memory (Current Session)",
        "l2": "Short-term Memory (Recent Sessions)",
        "l3": "Long-term Memory (Core Knowledge)",
    }

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH):
        """
        Initialize context formatter

        Args:
            max_length: Maximum context length in characters
        """
        self.max_length = max_length

    def format(self, memories: List[Dict],
               include_source: bool = True,
               include_scores: bool = False,
               layer_grouping: bool = True) -> InjectedContext:
        """
        Format memories for injection

        Args:
            memories: List of memory dictionaries
            include_source: Include source file information
            include_scores: Include relevance scores
            layer_grouping: Group memories by layer

        Returns:
            InjectedContext with formatted text and metadata
        """
        warnings = []

        # Handle empty memories
        if not memories:
            return InjectedContext(
                formatted_text="",
                memory_count=0,
                total_length=0,
                layers_included=[],
            )

        # Group by layer if requested
        if layer_grouping:
            formatted = self._format_grouped(
                memories,
                include_source=include_source,
                include_scores=include_scores,
            )
        else:
            formatted = self._format_flat(
                memories,
                include_source=include_source,
                include_scores=include_scores,
            )

        # Check length and truncate if needed
        truncated = False
        if len(formatted) > self.max_length:
            truncated = True
            formatted = self._truncate(formatted, self.max_length)
            warnings.append(f"Context truncated to {self.max_length} characters")

        # Extract unique layers (handle both dict and MemoryResult)
        def get_layer(m):
            if hasattr(m, 'layer'):
                layer = m.layer
                return layer.value if hasattr(layer, 'value') else str(layer)
            else:
                return m.get("layer", "unknown")
        
        layers = list(set(get_layer(m) for m in memories))

        return InjectedContext(
            formatted_text=formatted,
            memory_count=len(memories),
            total_length=len(formatted),
            layers_included=layers,
            truncated=truncated,
            warnings=warnings,
        )

    def _format_grouped(self, memories: List[Dict],
                        include_source: bool,
                        include_scores: bool) -> str:
        """Format memories grouped by layer"""
        # Group memories by layer
        by_layer: Dict[str, List] = {}
        for memory in memories:
            # Handle both dict and MemoryResult objects
            if hasattr(memory, 'layer'):
                layer = memory.layer or "unknown"
                content = memory.content
            else:
                layer = memory.get("layer") or "unknown"
                content = memory.get("content", "")
            
            if layer not in by_layer:
                by_layer[layer] = []
            by_layer[layer].append(memory)

        # Format each layer
        sections = []
        sections.append("--- Retrieved Context ---")

        for layer, layer_memories in sorted(by_layer.items()):
            # Handle MemoryLayer enum
            layer_str = layer.value if hasattr(layer, 'value') else str(layer)
            layer_name = self.LAYER_NAMES.get(layer_str, layer_str.upper())
            sections.append(f"\n## {layer_name}")

            for i, memory in enumerate(layer_memories, 1):
                entry = self._format_memory_entry(
                    memory,
                    index=i,
                    include_source=include_source,
                    include_scores=include_scores,
                )
                sections.append(entry)

        sections.append("--- End Retrieved Context ---\n")

        return "\n".join(sections)

    def _format_flat(self, memories: List[Dict],
                     include_source: bool,
                     include_scores: bool) -> str:
        """Format memories in a flat list"""
        sections = []
        sections.append("--- Retrieved Context ---")

        for i, memory in enumerate(memories, 1):
            entry = self._format_memory_entry(
                memory,
                index=i,
                include_source=include_source,
                include_scores=include_scores,
            )
            sections.append(entry)

        sections.append("--- End Retrieved Context ---\n")

        return "\n".join(sections)

    def _format_memory_entry(self, memory: Dict,
                             index: int,
                             include_source: bool,
                             include_scores: bool) -> str:
        """
        Format a single memory entry

        Args:
            memory: Memory dictionary
            index: Entry index
            include_source: Include source information
            include_scores: Include score

        Returns:
            Formatted entry string
        """
        # Handle both dict and MemoryResult objects
        if hasattr(memory, 'content'):
            content = memory.content
            layer = (memory.layer or "unknown")
            memory_id = memory.memory_id if hasattr(memory, 'memory_id') else ""
            source = memory.source if hasattr(memory, 'source') else ""
            score = memory.score if hasattr(memory, 'score') else None
            tags = memory.tags if hasattr(memory, 'tags') else []
            timestamp = memory.timestamp if hasattr(memory, 'timestamp') else None
        else:
            content = memory.get("content", "")
            layer = memory.get("layer") or "unknown"
            memory_id = memory.get("memory_id", "")
            source = memory.get("source", "")
            score = memory.get("score")
            tags = memory.get("tags", [])
            timestamp = memory.get("timestamp")
        
        layer = layer.value.upper() if hasattr(layer, 'value') else layer.upper()

        # Build entry header
        parts = [f"[{layer}-{index}]"]

        if include_scores and score is not None:
            parts.append(f"(relevance: {score:.3f})")

        # Format content with proper escaping
        escaped_content = self._escape_content(content)

        entry = " ".join(parts) + " " + escaped_content

        # Add metadata
        metadata = []

        if include_source and source and source != "working_memory":
            # Extract just the filename
            import os
            filename = os.path.basename(source)
            metadata.append(f"Source: {filename}")

        if tags:
            metadata.append(f"Tags: {', '.join(tags)}")

        if timestamp:
            # Format timestamp nicely
            metadata.append(f"Time: {timestamp}")

        if metadata:
            entry += "\n    " + " | ".join(metadata)

        return entry

    def _escape_content(self, content: str) -> str:
        """
        Escape special characters in content

        Args:
            content: Raw content

        Returns:
            Escaped content
        """
        # Remove control characters except newlines and tabs
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)

        # Normalize multiple newlines to double newline
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Strip leading/trailing whitespace per line
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)

        # Truncate very long individual entries
        if len(content) > 1000:
            content = content[:1000] + "..."

        return content

    def _truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text to max length

        Tries to cut at a sensible boundary (paragraph or sentence).

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Try to cut at section boundary first
        sections = text.split("--- End Retrieved Context ---")
        if len(sections) > 1:
            # Reconstruct with truncated content
            main_text = sections[0]
            if len(main_text) + 30 <= max_length:  # 30 for ending marker
                return main_text + "\n... (content truncated)\n--- End Retrieved Context ---\n"

        # Cut at max length and add ellipsis
        truncated = text[:max_length - 3] + "...\n... (content truncated)"

        return truncated


class ContextInjector:
    """
    Main context injection orchestrator

    Coordinates retrieval and formatting for prompt injection.
    """

    def __init__(self, formatter: Optional[ContextFormatter] = None):
        """
        Initialize context injector

        Args:
            formatter: Context formatter (created by default if None)
        """
        self.formatter = formatter or ContextFormatter()

    def inject(self, memories: List[Dict],
               template: Optional[str] = None) -> InjectedContext:
        """
        Inject memories into context

        Args:
            memories: Retrieved memories to inject
            template: Optional template for formatting

        Returns:
            InjectedContext with formatted result
        """
        # Use custom template if provided
        if template:
            formatted = self._apply_template(memories, template)
            layers = list(set(m.get("layer", "unknown") for m in memories))

            return InjectedContext(
                formatted_text=formatted,
                memory_count=len(memories),
                total_length=len(formatted),
                layers_included=layers,
            )

        # Use default formatter
        return self.formatter.format(memories)

    def _apply_template(self, memories: List[Dict], template: str) -> str:
        """
        Apply custom template to memories

        Template variables:
        - {{memories}}: List of formatted memories
        - {{count}}: Number of memories
        - {{layers}}: Comma-separated layer names

        Args:
            memories: Memory dictionaries
            template: Template string

        Returns:
            Formatted template
        """
        # Format memories
        memory_texts = []
        for memory in memories:
            content = memory.get("content", "")
            layer = memory.get("layer", "unknown").upper()
            memory_texts.append(f"[{layer}] {content}")

        memories_text = "\n".join(memory_texts)
        layers = ", ".join(set(m.get("layer", "unknown") for m in memories))

        # Apply template
        result = template
        result = result.replace("{{memories}}", memories_text)
        result = result.replace("{{count}}", str(len(memories)))
        result = result.replace("{{layers}}", layers)

        return result

    def create_system_prompt(self, base_prompt: str,
                             memories: List[Dict]) -> str:
        """
        Create system prompt with injected memories

        Args:
            base_prompt: Base system prompt
            memories: Retrieved memories

        Returns:
            Complete system prompt with context
        """
        # Format context
        context_result = self.inject(memories)

        if not context_result.formatted_text:
            # No context to inject
            return base_prompt

        # Inject after base prompt
        full_prompt = f"""{base_prompt}

{context_result.formatted_text}
"""

        return full_prompt


def format_memory_context(memories: List[Dict],
                          max_length: int = 4000,
                          group_by_layer: bool = True) -> str:
    """
    Convenience function to format memory context

    Args:
        memories: Retrieved memories
        max_length: Maximum context length
        group_by_layer: Group by memory layer

    Returns:
        Formatted context string
    """
    formatter = ContextFormatter(max_length=max_length)
    result = formatter.format(memories, layer_grouping=group_by_layer)

    return result.formatted_text


def inject_memories_to_prompt(memories: List[Dict],
                              base_prompt: str) -> str:
    """
    Convenience function to inject memories into prompt

    Args:
        memories: Retrieved memories
        base_prompt: Base system prompt

    Returns:
        Complete prompt with injected context
    """
    injector = ContextInjector()
    return injector.create_system_prompt(base_prompt, memories)
