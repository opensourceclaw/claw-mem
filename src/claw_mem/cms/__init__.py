# Copyright 2026 Peter Cheng
"""CMS (Context Management System) — v3.0.0-rc.1~rc.3."""

from .capacity_monitor import CapacityMonitor, CapacityStats, CapacityTrend
from .context_warning_hook import ContextWarningHook, WarningEvent
from .importance_evaluator import (
    ImportanceEvaluator,
    ImportanceScore,
    TYPE_IMPORTANCE,
)
from .compression_result import (
    SessionSummary,
    DeduplicationResult,
    CompressionPlan,
    CompressionResult,
)
from .session_summary import SessionSummaryGenerator
from .memory_deduplicator import MemoryDeduplicator
from .compression_strategy import CompressionStrategySelector
from .state_machine import SessionStateMachine, SessionState, StateEvent, StateTransition
from .context_switcher import ContextSwitcher, SwitchResult, MergeResult
from .recovery import RecoveryMechanism, RecoveryResult, ValidationResult
from .snapshot import SnapshotStorage, SessionSnapshot, SnapshotInfo

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
