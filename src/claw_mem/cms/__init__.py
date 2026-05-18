# Copyright 2026 Peter Cheng
"""CMS (Context Management System) — v3.0.0-rc.1 + v3.0.0-rc.2."""

from .capacity_monitor import CapacityMonitor, CapacityStats, CapacityTrend
from .context_warning_hook import ContextWarningHook, WarningEvent
from .importance_evaluator import (
    ImportanceEvaluator, ImportanceScore, TYPE_IMPORTANCE,
)
from .compression_result import (
    SessionSummary, DeduplicationResult,
    CompressionPlan, CompressionResult,
)
from .session_summary import SessionSummaryGenerator
from .memory_deduplicator import MemoryDeduplicator
from .compression_strategy import CompressionStrategySelector

__all__ = [
    # Phase 1
    'CapacityMonitor', 'CapacityStats', 'CapacityTrend',
    'ContextWarningHook', 'WarningEvent',
    'ImportanceEvaluator', 'ImportanceScore', 'TYPE_IMPORTANCE',
    # Phase 2
    'SessionSummary', 'DeduplicationResult',
    'CompressionPlan', 'CompressionResult',
    'SessionSummaryGenerator', 'MemoryDeduplicator',
    'CompressionStrategySelector',
]
