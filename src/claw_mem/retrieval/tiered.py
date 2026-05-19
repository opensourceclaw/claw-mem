# Copyright 2026 Peter Cheng
"""TieredRetriever — consolidated three-tier retrieval (v3.0.0).

Formerly three_tier.py. Provides STM/LTM/Archive memory retrieval.
"""

import warnings

from .three_tier import (
    ThreeTierRetriever,
    MemoryLayer,
    MemoryResult,
    SessionStartupHook,
    search_memory,
)

# TieredRetriever is the new name for ThreeTierRetriever
TieredRetriever = ThreeTierRetriever

warnings.warn(
    "three_tier module is deprecated. Import from tiered instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "TieredRetriever",
    "ThreeTierRetriever",
    "MemoryLayer",
    "MemoryResult",
    "SessionStartupHook",
    "search_memory",
]
