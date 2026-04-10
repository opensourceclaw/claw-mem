"""
Locomo Evaluation Framework for claw-mem

Evaluates claw-mem's long-term conversational memory using LoCoMo benchmark.
"""

__version__ = "0.1.0"

from .data_loader import LocomoDataLoader
from .agent import NeoClawAgent
from .eval import LocomoEvaluator

__all__ = [
    "LocomoDataLoader",
    "NeoClawAgent",
    "LocomoEvaluator",
]
