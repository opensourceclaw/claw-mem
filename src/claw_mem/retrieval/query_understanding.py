# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Query Understanding Module (P0-1 Stage 1)

Provides query expansion, intent classification, and entity extraction
to improve retrieval accuracy. Part of the three-stage retrieval pipeline.

Target: retrieval accuracy ~70% → ~91%
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .synonym_expander import SynonymExpander, get_synonym_expander


class QueryIntent(Enum):
    """Query intent types for retrieval strategy selection."""
    FACT = "fact"            # Looking for specific information
    RECENT = "recent"        # Looking for recent events
    PREFERENCE = "preference"  # Looking for user preferences
    PROCEDURE = "procedure"  # Looking for how-to steps / workflows
    GENERAL = "general"      # General purpose query


@dataclass
class ExpandedQuery:
    """Result of query understanding with expansions and metadata."""
    original: str
    expanded_text: str
    intent: QueryIntent
    entities: List[str] = field(default_factory=list)
    confidence: float = 0.0
    tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "original": self.original,
            "expanded_text": self.expanded_text,
            "intent": self.intent.value,
            "entities": self.entities,
            "confidence": self.confidence,
            "tokens": self.tokens,
        }


class QueryUnderstanding:
    """Stage 1: Understand and expand query for improved retrieval.

    Combines three strategies:
    1. Query expansion (synonyms, entity linking)
    2. Intent classification (fact/recent/preference/procedure)
    3. Entity extraction

    Usage:
        qu = QueryUnderstanding()
        expanded = qu.understand("what is my preferred AI framework?")
        # -> ExpandedQuery(intent=PREFERENCE, entities=["AI", "framework"], ...)
    """

    # Intent pattern definitions (bilingual: EN + ZH)
    INTENT_PATTERNS: Dict[QueryIntent, List[str]] = {
        QueryIntent.RECENT: [
            r"(?i)\b(recent|latest|last|yesterday|today|just|newly|recently)\b",
            r"(最近|刚刚|最新|昨天|今天|刚才|近期)",
        ],
        QueryIntent.PREFERENCE: [
            r"(?i)\b(prefer|preference|favorite|like|love|hate|dislike|best|worst)\b",
            r"(喜欢|偏好|最爱|习惯|讨厌|最好|最差|推荐|prefer)",
        ],
        QueryIntent.PROCEDURE: [
            r"(?i)\b(how|steps|procedure|process|workflow|guide|instruction|setup|configure)\b",
            r"(怎么|如何|步骤|流程|设置|配置|教程|指南|怎样)",
        ],
        QueryIntent.FACT: [
            r"(?i)\b(what|who|where|when|which|define|explain|describe|why)\b",
            r"(什么|谁|哪里|什么时候|哪个|定义|解释|为什么)",
        ],
    }

    # Entity extraction patterns
    ENTITY_PATTERNS: List[Tuple[str, str]] = [
        (r"(?i)\b(project|repo)[:\s]*['\"]?(\w[\w.-]*)['\"]?", "project"),
        (r"(?i)\b(version|ver)[:\s]*[vV]?(\d+\.\d+(?:\.\d+)?)", "version"),
        (r"(?i)\b(?:file|path)[:\s]*['\"]?([/\w.\\-]+\.\w+)['\"]?", "file_path"),
        (r"(?i)\b(?:branch)[:\s]*['\"]?([\w/-]+)['\"]?", "branch"),
        (r"(?i)\b(?:tag)[:\s]*['\"]?([\w.]+)['\"]?", "tag"),
        (r"(?i)\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b", "camel_case"),
        (r"(?i)\b(claw-\w+|openclaw|neoclaw|devclaw|workclaw|deepclaw)\b", "system"),
    ]

    def __init__(self, synonym_expander: Optional[SynonymExpander] = None):
        self._synonym_expander = synonym_expander or get_synonym_expander()
        self._intent_classifier = _IntentClassifier(self.INTENT_PATTERNS)
        self._entity_extractor = _EntityExtractor(self.ENTITY_PATTERNS)
        self._stats = {"queries_processed": 0, "intents": {}}

    def understand(self, query: str, context: Optional[Dict] = None) -> ExpandedQuery:
        """Understand and expand a query.

        Args:
            query: Raw user query string
            context: Optional conversation context dict

        Returns:
            ExpandedQuery with expansions, intent, and entities
        """
        self._stats["queries_processed"] += 1

        # Step 1: Expand query with synonyms
        expanded_text = self._synonym_expander.expand(query)

        # Step 2: Classify intent
        intent, intent_confidence = self._intent_classifier.classify(query)
        self._stats["intents"][intent.value] = self._stats["intents"].get(intent.value, 0) + 1

        # Step 3: Extract entities
        entities = self._entity_extractor.extract(query)

        # Step 4: Tokenize for retrieval
        tokens = self._tokenize(query)

        # Adjust intent based on context if available
        if context and intent == QueryIntent.GENERAL:
            context_intent = self._infer_from_context(context)
            if context_intent != QueryIntent.GENERAL:
                intent = context_intent
                intent_confidence = 0.6  # Lower confidence for context-inferred

        return ExpandedQuery(
            original=query,
            expanded_text=expanded_text,
            intent=intent,
            entities=entities,
            confidence=intent_confidence,
            tokens=tokens,
        )

    def expand_query(self, query: str) -> str:
        """Expand query with synonyms only.

        Args:
            query: Original search query

        Returns:
            Expanded query string
        """
        return self._synonym_expander.expand(query)

    def classify_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """Classify query intent.

        Args:
            query: Query string

        Returns:
            Tuple of (QueryIntent, confidence)
        """
        return self._intent_classifier.classify(query)

    def extract_entities(self, query: str) -> List[str]:
        """Extract named entities from query.

        Args:
            query: Query text

        Returns:
            List of extracted entity strings
        """
        return self._entity_extractor.extract(query)

    def get_statistics(self) -> Dict:
        """Get query understanding statistics."""
        return {
            "queries_processed": self._stats["queries_processed"],
            "intent_distribution": self._stats["intents"],
        }

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text for retrieval."""
        # Extract CJK characters
        cjk = re.findall(r'[\u4e00-\u9fff]', text)
        # Extract word tokens
        words = re.findall(r'\b\w+\b', text.lower())
        return cjk + words

    @staticmethod
    def _infer_from_context(context: Dict) -> QueryIntent:
        """Infer intent from conversation context."""
        recent_messages = context.get("recent_messages", [])
        recent_text = " ".join(recent_messages[-3:]) if recent_messages else ""

        if re.search(r"(决定|选择|偏好|喜欢)", recent_text):
            return QueryIntent.PREFERENCE
        if re.search(r"(怎么|如何|步骤|setup|configure)", recent_text):
            return QueryIntent.PROCEDURE
        if re.search(r"(?i)\b(what|who|where|when|什么)\b", recent_text):
            return QueryIntent.FACT
        return QueryIntent.GENERAL


class _IntentClassifier:
    """Internal: Pattern-based intent classifier."""

    def __init__(self, patterns: Dict[QueryIntent, List[str]]):
        self._patterns = patterns
        self._compiled: Dict[QueryIntent, List[re.Pattern]] = {}
        for intent, pat_list in patterns.items():
            self._compiled[intent] = [re.compile(p) for p in pat_list]

    def classify(self, query: str) -> Tuple[QueryIntent, float]:
        """Classify query using pattern matching.

        Returns:
            Tuple of (QueryIntent, confidence 0.0-1.0)
        """
        scores: Dict[QueryIntent, int] = {}
        for intent, patterns in self._compiled.items():
            matches = sum(1 for p in patterns if p.search(query))
            if matches > 0:
                scores[intent] = matches

        if not scores:
            return QueryIntent.GENERAL, 0.3

        # Return highest-scoring intent
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        total_score = sum(scores.values())

        # Confidence: how dominant is this intent?
        confidence = min(1.0, max_score / max(total_score, 1))
        return best_intent, confidence


class _EntityExtractor:
    """Internal: Regex-based entity extractor."""

    def __init__(self, patterns: List[Tuple[str, str]]):
        self._patterns = [(re.compile(p), label) for p, label in patterns]

    def extract(self, text: str) -> List[str]:
        """Extract entities from text.

        Returns:
            List of unique entity strings (deduplicated)
        """
        entities: Set[str] = set()
        for pattern, label in self._patterns:
            for match in pattern.findall(text):
                if isinstance(match, tuple):
                    # Group-based patterns: take the captured group
                    entity = match[1] if len(match) > 1 else match[0]
                else:
                    entity = match
                if entity and len(entity) > 1:
                    entities.add(entity.lower())
        return list(entities)


__all__ = [
    'QueryUnderstanding',
    'QueryIntent',
    'ExpandedQuery',
]
