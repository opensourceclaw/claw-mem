"""
Write-Time Gating Module

Intelligent memory storage system based on Selective Memory paper.

Core idea:
    Only store salient information, avoid memory redundancy.
    Use multi-dimensional salience scoring to determine storage tier.

Architecture:
    ┌─────────────────────────────────────┐
    │         WriteTimeGating             │
    │  ┌─────────────────────────────┐   │
    │  │     SalienceScorer          │   │
    │  │  - Source reputation (40%)  │   │
    │  │  - Novelty (30%)             │   │
    │  │  - Reliability (30%)         │   │
    │  └─────────────────────────────┘   │
    │              ↓                      │
    │  ┌──────────┐    ┌──────────┐      │
    │  │ Active   │    │  Cold    │      │
    │  │ Memory   │    │ Storage  │      │
    │  └──────────┘    └──────────┘      │
    └─────────────────────────────────────┘

Main classes:
    WriteTimeGating: Write-time gating controller
    SalienceScorer: Salience scorer
    InMemoryStorage: Active memory storage
    DiskStorage: Cold storage
    VersionChain: Version chain management
    GatingResult: Gating result

Usage:
    >>> from claw_mem.gating import WriteTimeGating
    >>>
    >>> # Create gating controller
    >>> gating = WriteTimeGating(threshold=0.6)
    >>>
    >>> # Write high-salience information
    >>> result = gating.write({
    ...     'content': 'important decision...',
    ...     'source': 'user',
    ...     'context': {'topic': 'tech stack selection'},
    ...     'verified': True
    ... })
    >>>
    >>> print(f"Storage tier: {result.tier}")  # 'active'
    >>> print(f"Salience: {result.salience_score:.2f}")  # 0.85
    >>>
    >>> # View statistics
    >>> stats = gating.get_stats()
    >>> print(f"Active memories: {stats['active_count']}")
    >>> print(f"Cold storage: {stats['cold_count']}")

Performance:
    - Write latency: < 10ms (measured ~0.5ms)
    - Scoring latency: < 5ms (measured ~0.02ms)
    - Memory usage: < 10MB (measured < 5MB)

References:
    Selective Memory: Learning what to remember

Version:
    Since: claw-mem v2.1.0
"""

from .write_time_gating import (
    AdaptiveThreshold,
    DiskStorage,
    GatingFilter,
    GatingFilterResult,
    GatingResult,
    InMemoryStorage,
    SalienceScorer,
    VersionChain,
    WriteTimeGating,
)

__all__ = [
    "WriteTimeGating",
    "SalienceScorer",
    "GatingResult",
    "InMemoryStorage",
    "DiskStorage",
    "VersionChain",
    "GatingFilter",
    "GatingFilterResult",
    "AdaptiveThreshold",
]
