# claw-mem v2.10.0 - Weight Consolidation Module
#
# Implements θ-Engineering: weight consolidation from episodic experiences.
# Based on "Contextual Agentic Memory is a Memo, Not True Memory" (arXiv:2604.27707)
#
# Architecture:
#   C-Engineering (Retrieval)  +  θ-Engineering (Weight) = True Memory

from .experience_classifier import ExperienceClassifier, ExperienceScore, ClassificationResult
from .weight_consolidator import WeightConsolidator, ConsolidationConfig
from .experience_queue import ExperienceQueue, QueueItem
from .daemon import ConsolidationDaemon, DaemonConfig
from .injection_detector import InjectionDetector, InjectionResult

__all__ = [
    "ExperienceClassifier", "ExperienceScore", "ClassificationResult",
    "WeightConsolidator", "ConsolidationConfig",
    "ExperienceQueue", "QueueItem",
    "ConsolidationDaemon", "DaemonConfig",
    "InjectionDetector", "InjectionResult",
]
