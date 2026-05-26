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
LLM Extractors - LLM-driven fact and concept extractors

Supports:
- LLM-driven intelligent extraction
- Rule-based fallback extraction
- Dummy extractor (for testing)
"""

import re
from abc import ABC, abstractmethod
from typing import Any, List


class BaseExtractor(ABC):
    """Extractor base class"""

    @abstractmethod
    def extract_facts(self, text: str) -> List[str]:
        """Extract facts"""

    @abstractmethod
    def extract_concepts(self, text: str) -> List[str]:
        """Extract concepts"""


class LLMExtractor(BaseExtractor):
    """LLM-driven extractor

    Supports multiple LLM clients (OpenAI, Anthropic, local models, etc.).
    Uses rule-based fallback when no LLM is available.
    """

    def __init__(self, llm_client: Any = None):
        """
        Args:
            llm_client: LLM client (supports .generate(prompt) method)
        """
        self.llm = llm_client

    def extract_facts(self, text: str) -> List[str]:
        """Extract key facts from text

        Args:
            text: Input text

        Returns:
            List[str]: List of facts
        """
        if not self.llm:
            return self._extract_facts_rule_based(text)

        prompt = self._build_facts_prompt(text)

        try:
            response = self._call_llm(prompt)
            facts = self._parse_lines(response)
            return facts
        except Exception:
            # Fall back to rule-based extraction
            return self._extract_facts_rule_based(text)

    def extract_concepts(self, text: str) -> List[str]:
        """Extract core concepts from text

        Args:
            text: Input text

        Returns:
            List[str]: List of concepts
        """
        if not self.llm:
            return self._extract_concepts_rule_based(text)

        prompt = self._build_concepts_prompt(text)

        try:
            response = self._call_llm(prompt)
            concepts = self._parse_lines(response)
            return concepts
        except Exception:
            # Fall back to rule-based extraction
            return self._extract_concepts_rule_based(text)

    def generate_reflection(self, nodes: List[Any]) -> str:
        """Generate reflection from nodes

        Args:
            nodes: List of source nodes

        Returns:
            str: Reflection content
        """
        if not self.llm:
            return self._generate_reflection_rule_based(nodes)

        prompt = self._build_reflection_prompt(nodes)

        try:
            return self._call_llm(prompt)
        except Exception:
            return self._generate_reflection_rule_based(nodes)

    def _call_llm(self, prompt: str) -> str:
        """Call LLM"""
        if hasattr(self.llm, "generate"):
            return self.llm.generate(prompt)
        elif hasattr(self.llm, "chat"):
            return self.llm.chat(prompt)
        else:
            raise ValueError("LLM client must have 'generate' or 'chat' method")

    def _parse_lines(self, response: str) -> List[str]:
        """Parse LLM response into list of lines"""
        lines = response.strip().split("\n")
        return [line.strip().strip("-* ").strip() for line in lines if line.strip()]

    def _build_facts_prompt(self, text: str) -> str:
        """Build fact extraction prompt"""
        return f"""Extract key facts from the following text.

Requirements:
1. One fact per line
2. Only extract objective facts, do not infer
3. Keep it concise

Text:
{text}

Fact list:"""

    def _build_concepts_prompt(self, text: str) -> str:
        """Build concept extraction prompt"""
        return f"""Extract core concepts from the following text.

Requirements:
1. One concept per line
2. Extract keywords, topics, entities
3. Keep it concise

Text:
{text}

Concept list:"""

    def _build_reflection_prompt(self, nodes: List[Any]) -> str:
        """Build reflection generation prompt"""
        node_contents = "\n".join([f"- {n.content}" for n in nodes[:10]])
        return f"""Generate a brief reflection summary based on the following memory nodes:

{node_contents}

Reflection:"""

    def _extract_facts_rule_based(self, text: str) -> List[str]:
        """Rule-based fact extraction (fallback)

        Split text by sentences, extract complete sentences as facts.
        """
        # Split by common separators
        sentences = re.split(r"[.!?.!?\n]+", text)
        facts = []
        for s in sentences:
            s = s.strip()
            # Filter too short or too long
            if 5 < len(s) < 200:
                facts.append(s)
        return facts[:5]  # Max 5

    def _extract_concepts_rule_based(self, text: str) -> List[str]:
        """Rule-based concept extraction (fallback)

        Extract Chinese words (2-4 chars) and English words as concepts.
        """
        # Chinese words (2-4 chars)
        chinese = re.findall(r"[\u4e00-\u9fa5]{2,4}", text)

        # English words (3+ letters)
        english = re.findall(r"[a-zA-Z]{3,}", text)

        # Merge and deduplicate
        concepts = list(set(chinese + english))
        return concepts[:10]  # Max 10

    def _generate_reflection_rule_based(self, nodes: List[Any]) -> str:
        """Rule-based reflection generation (fallback)"""
        if not nodes:
            return "Not enough information to generate reflection"

        # Simple strategy: take the latest node content
        latest = nodes[-1] if nodes else None
        if latest:
            return f"Review: {latest.content[:100]}"
        return "Not enough information to generate reflection"


class DummyExtractor(BaseExtractor):
    """Dummy extractor (for testing)"""

    def extract_facts(self, text: str) -> List[str]:
        """Return empty list"""
        return []

    def extract_concepts(self, text: str) -> List[str]:
        """Return empty list"""
        return []


class KeywordExtractor(BaseExtractor):
    """Keyword extractor (lightweight approach)

    No LLM dependency, uses keyword extraction algorithm.
    """

    def __init__(self):
        self.stopwords = {
            "的",
            "了",
            "是",
            "在",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
        }

    def extract_facts(self, text: str) -> List[str]:
        """Use sentence splitting to extract facts"""
        return LLMExtractor()._extract_facts_rule_based(text)

    def extract_concepts(self, text: str) -> List[str]:
        """Extract keywords as concepts"""
        # Remove stopwords then extract
        words = re.findall(r"[\u4e00-\u9fa5]{2,4}|[a-zA-Z]{3,}", text)
        concepts = [w for w in words if w not in self.stopwords]
        return list(set(concepts))[:10]


__all__ = [
    "BaseExtractor",
    "LLMExtractor",
    "DummyExtractor",
    "KeywordExtractor",
]
