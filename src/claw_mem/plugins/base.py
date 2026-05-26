# Copyright 2026 Peter Cheng
"""
MemoryPlugin — Abstract base class for claw-mem plugins (v3.2.0).

Extensions like Compression, Engram, and Spreading can be implemented
as plugins that follow this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MemoryPlugin(ABC):
    """Abstract base class for memory system plugins.

    Plugins are self-contained extensions that hook into the core
    store/search/get_context pipeline. They are loaded/unloaded at
    runtime and can be composed by MemoryManager.

    Lifecycle:
        1. load(config)  — initialize the plugin
        2. invoke(...)   — called on each pipeline event
        3. unload()      — cleanup and shutdown
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier."""

    @abstractmethod
    def load(self, **kwargs) -> bool:
        """Initialize the plugin with provided configuration.

        Returns:
            True if initialization succeeded.
        """

    @abstractmethod
    def unload(self) -> None:
        """Release resources and perform cleanup."""

    def invoke(self, event: str, payload: Any = None, **kwargs) -> Any:
        """Handle a pipeline event.

        Args:
            event: Event name (e.g., "pre_store", "post_search", "shutdown").
            payload: Optional data to process.
            **kwargs: Additional context.

        Returns:
            Processed result, or None if the plugin ignores this event.
        """
        handler = getattr(self, f"on_{event}", None)
        if handler:
            return handler(payload, **kwargs)
        return None

    def get_metadata(self) -> Dict[str, str]:
        """Return plugin metadata for discovery."""
        return {"name": self.name, "version": "0.0.0"}

    def validate(self) -> List[str]:
        """Return a list of configuration errors (empty = valid)."""
        return []

    def __repr__(self) -> str:
        return f"<MemoryPlugin:{self.name}>"
