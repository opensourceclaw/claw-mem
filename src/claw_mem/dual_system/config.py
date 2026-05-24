"""
Dual system configuration for hippocampus-neocortex memory model.
"""

from dataclasses import dataclass, field


@dataclass
class DualSystemConfig:
    """Configuration for the dual-system memory model.

    Attributes:
        hippocampal_capacity: Max entries in hippocampal store.
        hippocampal_ttl_seconds: Time-to-live for hippocampal entries (default 24h).
        neocortical_capacity: Max entries in neocortical store.
        consolidation_interval_seconds: How often to run consolidation (default 1h).
        consolidation_batch_size: Max memories to consolidate per cycle.
        importance_threshold: Minimum importance to queue for consolidation.
        forgetting_curve_enabled: Apply Ebbinghaus forgetting curve.
        background_consolidation: Run consolidation in background thread.
        lru_cache_size: Size of hippocampal LRU cache.
    """

    hippocampal_capacity: int = 10000
    hippocampal_ttl_seconds: int = 86400  # 24 hours
    neocortical_capacity: int = 100000
    consolidation_interval_seconds: int = 3600  # 1 hour
    consolidation_batch_size: int = 100
    importance_threshold: float = 0.3
    forgetting_curve_enabled: bool = True
    background_consolidation: bool = False
    lru_cache_size: int = 1000

    def to_dict(self) -> dict:
        return {
            "hippocampal_capacity": self.hippocampal_capacity,
            "hippocampal_ttl_seconds": self.hippocampal_ttl_seconds,
            "neocortical_capacity": self.neocortical_capacity,
            "consolidation_interval_seconds": self.consolidation_interval_seconds,
            "consolidation_batch_size": self.consolidation_batch_size,
            "importance_threshold": self.importance_threshold,
            "forgetting_curve_enabled": self.forgetting_curve_enabled,
            "background_consolidation": self.background_consolidation,
            "lru_cache_size": self.lru_cache_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DualSystemConfig":
        return cls(
            hippocampal_capacity=data.get("hippocampal_capacity", 10000),
            hippocampal_ttl_seconds=data.get("hippocampal_ttl_seconds", 86400),
            neocortical_capacity=data.get("neocortical_capacity", 100000),
            consolidation_interval_seconds=data.get("consolidation_interval_seconds", 3600),
            consolidation_batch_size=data.get("consolidation_batch_size", 100),
            importance_threshold=data.get("importance_threshold", 0.3),
            forgetting_curve_enabled=data.get("forgetting_curve_enabled", True),
            background_consolidation=data.get("background_consolidation", False),
            lru_cache_size=data.get("lru_cache_size", 1000),
        )
