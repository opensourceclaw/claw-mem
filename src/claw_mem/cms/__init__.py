# Copyright 2026 Peter Cheng
"""CMS (Context Management System) — v3.0.0-rc.1~rc.3."""

from .capacity_monitor import CapacityMonitor, CapacityStats, CapacityTrend
from .compression_result import (
    CompressionPlan,
    CompressionResult,
    DeduplicationResult,
    SessionSummary,
)
from .compression_strategy import CompressionStrategySelector
from .context_switcher import ContextSwitcher, MergeResult, SwitchResult
from .context_warning_hook import ContextWarningHook, WarningEvent
from .importance_evaluator import TYPE_IMPORTANCE, ImportanceEvaluator, ImportanceScore
from .memory_deduplicator import MemoryDeduplicator
from .recovery import RecoveryMechanism, RecoveryResult, ValidationResult
from .session_summary import SessionSummaryGenerator
from .snapshot import SessionSnapshot, SnapshotInfo, SnapshotStorage
from .state_machine import SessionState, SessionStateMachine, StateEvent, StateTransition

__all__ = [
    # Phase 1
    "CapacityMonitor",
    "CapacityStats",
    "CapacityTrend",
    "ContextWarningHook",
    "WarningEvent",
    "ImportanceEvaluator",
    "ImportanceScore",
    "TYPE_IMPORTANCE",
    # Phase 2
    "SessionSummary",
    "DeduplicationResult",
    "CompressionPlan",
    "CompressionResult",
    "SessionSummaryGenerator",
    "MemoryDeduplicator",
    "CompressionStrategySelector",
    # Phase 3
    "SessionStateMachine",
    "SessionState",
    "StateEvent",
    "StateTransition",
    "ContextSwitcher",
    "SwitchResult",
    "MergeResult",
    "RecoveryMechanism",
    "RecoveryResult",
    "ValidationResult",
    "SnapshotStorage",
    "SessionSnapshot",
    "SnapshotInfo",
]
