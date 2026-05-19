# Copyright 2026 Peter Cheng
# Licensed under the Apache License, Version 2.0
"""SmartRetriever — consolidation of heuristic, smart, enhanced, decoupled."""

import warnings

# Re-export old classes with deprecation
from .heuristic_retriever import HeuristicRetriever, SmartRetriever, HeuristicConfig

warnings.warn(
    "Importing from heuristic_retriever is deprecated. "
    "Use claw_mem.retrieval.smart import SmartRetriever instead.",
    DeprecationWarning, stacklevel=2,
)

from .enhanced_smart_retriever import EnhancedSmartRetriever
from .decoupled import DecoupledRetriever

__all__ = [
    "SmartRetriever",
    "HeuristicRetriever",
    "HeuristicConfig",
    "EnhancedSmartRetriever",
    "DecoupledRetriever",
]
