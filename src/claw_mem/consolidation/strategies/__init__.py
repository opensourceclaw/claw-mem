# claw-mem v2.10.0 - Consolidation Strategies
#
# LoRA: Low-Rank Adaptation - efficient weight updates
# EWC: Elastic Weight Consolidation - protects important weights

from .ewc_strategy import EWCConfig, EWCStrategy
from .lora_strategy import LoRAConfig, LoRAStrategy

__all__ = ["LoRAStrategy", "LoRAConfig", "EWCStrategy", "EWCConfig"]
