# Context Injection Best Practices

**Version**: 1.0.0
**Date**: 2026-03-23
**Author**: Study Agent
**Status**: Complete

---

## Executive Summary

This document defines best practices for context injection in claw-mem v1.0.0. Context injection is the process of adding retrieved memories to the session prompt for the LLM. Based on research and the requirements in `claw-mem-v1.0.0-requirements.md`:

**Key Recommendations**:
1. Inject context at session startup (hook-based)
2. Format memories clearly with source attribution
3. Limit injected context to top 10 relevant memories
4. Handle edge cases (empty results, special characters)
5. Support manual refresh via `/search` command

---

## 1. Context Injection Flow

### 1.1 Session Startup Flow

```
┌─────────────────────────────────────────────────────────┐
│              Session Startup Context Injection           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. User starts new session                             │
│           │                                             │
│           ▼                                             │
│  2. Extract intent/topics from initial query            │
│           │                                             │
│           ▼                                             │
│  3. Search memories (L1/L2/L3) based on topics          │
│           │                                             │
│           ▼                                             │
│  4. Rank and filter results (top 10)                    │
│           │                                             │
│           ▼                                             │
│  5. Format memories into context string                 │
│           │                                             │
│           ▼                                             │
│  6. Inject into system prompt                           │
│           │                                             │
│           ▼                                             │
│  7. Session ready with context                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Code Implementation

```python
class ContextInjector:
    """Handle context injection for sessions"""

    MAX_CONTEXT_MEMORIES = 10
    MAX_CONTEXT_LENGTH = 4000  # Characters

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager

    def inject_context(self, session_id: str, initial_query: str = None) -> str:
        """
        Inject relevant memories into session context.

        Args:
            session_id: Unique session identifier
            initial_query: Optional initial user query for topic extraction

        Returns:
            Formatted context string for system prompt
        """
        # Step 1: Extract topics
        topics = self._extract_topics(initial_query) if initial_query else []

        # Step 2: Search memories
        memories = self.memory_manager.search(
            query=initial_query or "",
            limit=self.MAX_CONTEXT_MEMORIES
        )

        # Step 3: Format context
        context = self._format_context(memories, topics)

        # Step 4: Log injection
        self._log_injection(session_id, memories)

        return context

    def _extract_topics(self, query: str) -> List[str]:
        """Extract topic keywords from query"""
        # Simple keyword extraction (can be enhanced with NLP)
        # Remove stop words and extract nouns
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been'}
        words = query.lower().split()
        topics = [w for w in words if w not in stop_words and len(w) > 3]
        return topics[:5]  # Limit to 5 topics
```

---

## 2. Context Formatting

### 2.1 Recommended Format

```markdown
## Retrieved Context

The following memories are relevant to your current session:

---
**Source**: MEMORY.md (Long-term Memory)
**Relevance**: 0.92
**Content**: User prefers DD/MM/YYYY date format
---

---
**Source**: memory/2026-03-20.md (Short-term Memory)
**Relevance**: 0.85
**Content**: Discussed claw-mem architecture - 3-layer design (L1/L2/L3)
---

---
**Source**: memory/skills/deployment.md (Procedural Memory)
**Relevance**: 0.78
**Content**: Deployment process: 1) pytest 2) build 3) twine upload
---

*End of retrieved context (3 memories)*
```

### 2.2 Format Implementation

```python
def _format_context(self, memories: List[Memory], topics: List[str]) -> str:
    """Format memories into context string"""
    if not memories:
        return "## Retrieved Context\n\nNo relevant memories found for this session."

    lines = [
        "## Retrieved Context",
        "",
        f"The following memories are relevant to your current session",
        f"Topic: {', '.join(topics)}" if topics else "",
        ""
    ]

    for i, memory in enumerate(memories, 1):
        layer = self._get_layer_name(memory)
        relevance = memory.relevance_score if hasattr(memory, 'relevance_score') else 'N/A'

        lines.extend([
            "---",
            f"**Source**: {layer}",
            f"**Relevance**: {relevance}",
            f"**Content**: {memory.content}",
            "---",
            ""
        ])

    lines.append(f"*End of retrieved context ({len(memories)} memories)*")

    return "\n".join(lines)

def _get_layer_name(self, memory: Memory) -> str:
    """Get human-readable layer name"""
    layer_map = {
        'l1': 'Working Memory (Current Session)',
        'l2': 'Short-term Memory (Daily)',
        'l3': 'Long-term Memory (MEMORY.md)'
    }
    return layer_map.get(memory.layer, memory.layer)
```

---

## 3. Edge Case Handling

### 3.1 Empty Results

```python
def _format_context(self, memories: List[Memory], topics: List[str]) -> str:
    if not memories:
        return (
            "## Retrieved Context\n\n"
            "No relevant memories found for this session.\n"
            "You can use `/search <query>` to manually search for memories."
        )
    # ... rest of formatting
```

### 3.2 Special Character Escaping

```python
import html
import re

def escape_special_characters(content: str) -> str:
    """Escape special characters in memory content"""
    # Escape Markdown special characters if needed
    # content = re.sub(r'([*_`\\])', r'\\\1', content)

    # Remove or replace control characters
    content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)

    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content)

    return content.strip()
```

### 3.3 Context Length Limits

```python
def _format_context_with_limit(self, memories: List[Memory], max_length: int = 4000) -> str:
    """Format context with length limit"""
    lines = ["## Retrieved Context", ""]
    current_length = len("\n".join(lines))

    for memory in memories:
        memory_block = self._format_single_memory(memory)
        if current_length + len(memory_block) > max_length:
            lines.append(f"\n*... and {len(memories) - memories.index(memory)} more memories (truncated)*")
            break

        lines.append(memory_block)
        current_length += len(memory_block)

    return "\n".join(lines)
```

---

## 4. Integration with OpenClaw

### 4.1 Session Hook

```python
class OpenClawPlugin:
    """claw-mem plugin for OpenClaw"""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.context_injector = ContextInjector(memory_manager)

    def on_session_start(self, session_id: str, initial_message: str) -> dict:
        """
        Hook called when OpenClaw session starts.

        Returns:
            dict with 'system_prompt_addition' key
        """
        context = self.context_injector.inject_context(
            session_id=session_id,
            initial_query=initial_message
        )

        return {
            'system_prompt_addition': context,
            'session_metadata': {
                'context_injected': True,
                'memory_count': len(self._parse_memories(context))
            }
        }
```

### 4.2 Manual Search Command

```python
@memory_manager.command('/search')
def search_command(query: str, session_id: str) -> str:
    """
    Manual memory search command.

    Usage: /search <query>
    Example: /search deployment process
    """
    if not query:
        return "Please provide a search query. Usage: /search <query>"

    memories = self.memory_manager.search(query=query, limit=10)
    return self.context_injector._format_context(memories, topics=[])
```

---

## 5. Best Practices Checklist

### 5.1 Content Formatting

- [ ] Include source attribution (L1/L2/L3)
- [ ] Show relevance scores
- [ ] Escape special characters
- [ ] Truncate overly long memories
- [ ] Add clear section headers

### 5.2 Performance

- [ ] Limit results to 10 memories
- [ ] Set max context length (4000 chars)
- [ ] Cache formatted context for session
- [ ] Lazy-load additional memories on demand

### 5.3 User Experience

- [ ] Show "no results" message clearly
- [ ] Provide search command help
- [ ] Indicate when context is truncated
- [ ] Allow manual context refresh

### 5.4 Debugging

- [ ] Log all context injections
- [ ] Track which memories were injected
- [ ] Record injection latency
- [ ] Monitor context length distribution

---

## 6. Example Session Flow

### 6.1 Session Start

**User Input**: "How do I deploy claw-mem?"

**Context Injection**:
```
## Retrieved Context

The following memories are relevant to your current session:
Topic: deploy, claw-mem

---
**Source**: memory/skills/deployment.md (Procedural Memory)
**Relevance**: 0.92
**Content**: Deployment process: 1) Run pytest 2) Build with python -m build 3) Upload with twine upload dist/*
---

---
**Source**: MEMORY.md (Long-term Memory)
**Relevance**: 0.85
**Content**: claw-mem repository: https://github.com/opensourceclaw/claw-mem
---

*End of retrieved context (2 memories)*
```

**LLM Response** (with context):
```
Based on your stored memories, here's how to deploy claw-mem:

1. Run tests: `pytest`
2. Build: `python -m build`
3. Upload: `twine upload dist/*`

The claw-mem repository is at: https://github.com/opensourceclaw/claw-mem
```

### 6.2 No Results Case

**User Input**: "What did I say about quantum computing?"

**Context Injection** (no matches):
```
## Retrieved Context

No relevant memories found for this session.
You can use `/search quantum computing` to manually search for memories.
```

---

## 7. References

1. claw-mem-v1.0.0-requirements.md - REQ-001, REQ-002
2. ARCHITECTURE.md - Section 9: API Design
3. F2_LAZY_LOADING.md - Lazy loading integration

---

**Document History**:
| Date | Version | Change |
|------|---------|--------|
| 2026-03-23 | 1.0 | Initial best practices document |
