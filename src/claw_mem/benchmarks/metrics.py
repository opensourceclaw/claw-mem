"""
claw-mem v2.11.0 - Evaluation Metrics

Standard IR and memory evaluation metrics:
  Recall@K, MRR, Precision, Accuracy
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set
import math


@dataclass
class EvalResult:
    """Single evaluation result."""
    metric: str
    value: float
    k: int = 0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"metric": self.metric, "value": round(self.value, 4),
                "k": self.k}


@dataclass
class EvaluationMetrics:
    """Collection of evaluation metrics."""
    results: List[EvalResult] = field(default_factory=list)

    def add(self, metric: str, value: float, k: int = 0, desc: str = ""):
        self.results.append(EvalResult(metric=metric, value=value, k=k, description=desc))

    def get(self, metric: str) -> float:
        for r in self.results:
            if r.metric == metric:
                return r.value
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"metrics": [r.to_dict() for r in self.results]}


class RecallAtK:
    """Recall@K: fraction of relevant items found in top-K results."""

    @staticmethod
    def calculate(returned: List[str], relevant: Set[str], k: int = 10) -> float:
        if not relevant:
            return 1.0
        top_k = returned[:k]
        found = sum(1 for item in top_k if item in relevant)
        return found / len(relevant)

    @staticmethod
    def calculate_all(returned: List[str], relevant: Set[str],
                      ks: List[int] = None) -> List[EvalResult]:
        ks = ks or [1, 3, 5, 10]
        return [
            EvalResult(metric="recall", value=RecallAtK.calculate(returned, relevant, k), k=k)
            for k in ks
        ]


class MRR:
    """Mean Reciprocal Rank: 1 / rank of first relevant item."""

    @staticmethod
    def calculate(returned: List[str], relevant: Set[str]) -> float:
        for i, item in enumerate(returned, 1):
            if item in relevant:
                return 1.0 / i
        return 0.0

    @staticmethod
    def calculate_batch(queries: List[Dict]) -> float:
        """Calculate MRR over multiple queries.

        Each query dict: {"returned": [...], "relevant": set(...)}
        """
        if not queries:
            return 0.0
        return sum(MRR.calculate(q["returned"], q["relevant"]) for q in queries) / len(queries)


class Precision:
    """Precision: fraction of returned items that are relevant."""

    @staticmethod
    def calculate(returned: List[str], relevant: Set[str], k: int = 10) -> float:
        top_k = returned[:k]
        if not top_k:
            return 0.0
        found = sum(1 for item in top_k if item in relevant)
        return found / len(top_k)


class Accuracy:
    """Simple accuracy: correct / total."""

    @staticmethod
    def calculate(correct: int, total: int) -> float:
        if total == 0:
            return 0.0
        return correct / total
