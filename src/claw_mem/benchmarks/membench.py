"""
claw-mem v2.11.0 - MemBench Evaluation

Four dimensions of memory capability:
  1. Accurate Retrieval (Recall@K, MRR, Precision)
  2. Test-time Learning (few-shot accuracy)
  3. Long-range Understanding (cross-session consistency)
  4. Selective Forgetting (post-deletion residue check)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Optional

from .metrics import RecallAtK, MRR, Precision, EvalResult, EvaluationMetrics


@dataclass
class MemBenchConfig:
    ks: List[int] = field(default_factory=lambda: [1, 3, 5, 10])
    few_shot_examples: int = 3
    consistency_threshold: float = 0.8


@dataclass
class MemBenchResult:
    retrieval: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    test_time_learning: Dict[str, float] = field(default_factory=dict)
    long_range: Dict[str, float] = field(default_factory=dict)
    selective_forgetting: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "retrieval": self.retrieval.to_dict()["metrics"],
            "test_time_learning": self.test_time_learning,
            "long_range": self.long_range,
            "selective_forgetting": self.selective_forgetting,
        }


class MemBench:
    """MemBench memory capability evaluation.

    Usage:
        mb = MemBench()
        result = mb.evaluate_retrieval(returned_ids, relevant_ids)
        result = mb.evaluate_test_time_learning(tasks, accuracy)
        result = mb.evaluate_long_range(sessions)
        result = mb.evaluate_forgetting(before_ids, deleted_ids, after_ids)
    """

    def __init__(self, config: Optional[MemBenchConfig] = None):
        self.config = config or MemBenchConfig()

    def evaluate_retrieval(
        self, returned: List[str], relevant: Set[str]
    ) -> EvaluationMetrics:
        """Evaluate retrieval accuracy.

        Args:
            returned: Ordered list of returned item IDs
            relevant: Set of relevant item IDs

        Returns:
            EvaluationMetrics with recall, MRR, precision
        """
        metrics = EvaluationMetrics()

        # Recall@K
        for r in RecallAtK.calculate_all(returned, relevant, self.config.ks):
            metrics.add(f"recall@{r.k}", r.value, k=r.k)

        # MRR
        mrr_val = MRR.calculate(returned, relevant)
        metrics.add("mrr", mrr_val, k=0)

        # Precision@10
        prec_val = Precision.calculate(returned, relevant, k=10)
        metrics.add("precision@10", prec_val, k=10)

        return metrics

    def evaluate_test_time_learning(
        self, few_shot_accuracy: float
    ) -> Dict[str, float]:
        """Evaluate test-time (few-shot) learning capability.

        Args:
            few_shot_accuracy: Accuracy after few-shot examples
        """
        return {
            "few_shot_accuracy": round(few_shot_accuracy, 4),
            "examples_used": self.config.few_shot_examples,
        }

    def evaluate_long_range(
        self, session_consistency_scores: List[float]
    ) -> Dict[str, float]:
        """Evaluate long-range understanding.

        Args:
            session_consistency_scores: List of cross-session similarity scores
        """
        if not session_consistency_scores:
            return {"avg_consistency": 0.0, "sessions_compared": 0}
        return {
            "avg_consistency": round(sum(session_consistency_scores) / len(session_consistency_scores), 4),
            "sessions_compared": len(session_consistency_scores),
        }

    def evaluate_forgetting(
        self, pre_delete: Set[str], deleted: Set[str], post_delete: Set[str]
    ) -> Dict[str, float]:
        """Evaluate selective forgetting.

        Args:
            pre_delete: Items before deletion
            deleted: Items that should be deleted
            post_delete: Items after deletion
        """
        residue = deleted & post_delete
        return {
            "deleted_count": len(deleted),
            "residue_count": len(residue),
            "forget_rate": round(1.0 - len(residue) / len(deleted), 4) if deleted else 1.0,
        }
