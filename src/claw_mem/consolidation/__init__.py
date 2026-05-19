# claw-mem v2.10.0 - Weight Consolidation Module
#
# Implements θ-Engineering: weight consolidation from episodic experiences.
# Based on "Contextual Agentic Memory is a Memo, Not True Memory" (arXiv:2604.27707)
#
# Architecture:
#   C-Engineering (Retrieval)  +  θ-Engineering (Weight) = True Memory

from .daemon import ConsolidationDaemon, DaemonConfig
from .experience_classifier import ClassificationResult, ExperienceClassifier, ExperienceScore
from .experience_queue import ExperienceQueue, QueueItem
from .injection_detector import InjectionDetector, InjectionResult
from .weight_consolidator import ConsolidationConfig, WeightConsolidator

__all__ = [
    "ExperienceClassifier",
    "ExperienceScore",
    "ClassificationResult",
    "WeightConsolidator",
    "ConsolidationConfig",
    "ExperienceQueue",
    "QueueItem",
    "ConsolidationDaemon",
    "DaemonConfig",
    "InjectionDetector",
    "InjectionResult",
]
