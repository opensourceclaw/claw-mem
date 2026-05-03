# claw-mem v2.10.0 - Consolidation Strategies
#
# LoRA: Low-Rank Adaptation - efficient weight updates
# EWC: Elastic Weight Consolidation - protects important weights

from .lora_strategy import LoRAStrategy, LoRAConfig
from .ewc_strategy import EWCStrategy, EWCConfig

__all__ = ["LoRAStrategy", "LoRAConfig", "EWCStrategy", "EWCConfig"]
