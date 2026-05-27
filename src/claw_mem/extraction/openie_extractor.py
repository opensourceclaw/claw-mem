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
OpenIE Extractor (v4.10.0)

Dual-mode structured triplet extraction inspired by HippoRAG:
- LLM mode: high precision via structured prompt
- Rule mode: zero-dependency regex matching for Chinese and English text
"""

import json
import re
from dataclasses import dataclass
from typing import List

_LLM_SYSTEM_PROMPT = """\
You are a knowledge extraction engine. Extract ALL subject-predicate-object
triplets from the given text. A triplet captures a factual relationship
between two entities.

Output ONLY a JSON array of objects with these fields:
- "s": subject entity (string)
- "p": predicate / relationship (string)
- "o": object entity (string)
- "c": confidence score 0.0-1.0 (float)

Rules:
- Extract EVERY possible relationship, not just the main one
- Use concise entity names (proper nouns preferred)
- Predicates should be short descriptive verbs or phrases
- Set confidence based on how explicit the relationship is in the text
- Return empty array [] if no relationships found

Example:
Text: "张三是李四的上司。张三负责电商项目。"
Output: [
  {"s":"张三","p":"是...的上司","o":"李四","c":0.9},
  {"s":"张三","p":"负责","o":"电商项目","c":0.9}
]
"""


@dataclass
class Triplet:
    """A single subject-predicate-object triplet extracted from text.

    Attributes:
        subject: The subject entity.
        predicate: The relationship or verb.
        object: The object entity.
        confidence: Extraction confidence (0.0-1.0).
        source: Extraction source ("llm" or "rule").
    """
    subject: str
    predicate: str
    object: str
    confidence: float = 0.5
    source: str = "rule"

    def __repr__(self) -> str:
        return (
            f"Triplet({self.subject!r} -{self.predicate}-> {self.object!r},"
            f" c={self.confidence:.2f}, src={self.source})"
        )


class OpenIEExtractor:
    """Open Information Extraction engine with dual-mode support.

    Modes:
      - "llm": Use LLMProvider for high-precision extraction.
      - "rule": Use regex-based patterns (zero dependencies).
      - "auto": Try LLM first, fall back to rule on failure (default).

    Usage:
        extractor = OpenIEExtractor(llm_provider=llm, mode="auto")
        triplets = extractor.extract("张三是李四的上司。张三负责电商项目。")
    """

    def __init__(self, llm_provider=None, mode: str = "auto"):
        self._llm = llm_provider
        self._mode = mode if mode in ("llm", "rule", "auto") else "auto"

    # ── Public API ──────────────────────────────────────────────────────

    def extract(self, text: str) -> List[Triplet]:
        """Extract triplets from text using the configured mode.

        Args:
            text: Input text (Chinese or English).

        Returns:
            List of extracted Triplet objects.
        """
        if not text or not text.strip():
            return []

        text = text.strip()

        if self._mode == "llm":
            return self._extract_llm(text)
        elif self._mode == "rule":
            return self._extract_rule(text)
        else:  # auto
            if self._llm is not None:
                llm_results = self._extract_llm(text)
                if llm_results:
                    return llm_results
            return self._extract_rule(text)

    # ── LLM Mode ────────────────────────────────────────────────────────

    def _extract_llm(self, text: str) -> List[Triplet]:
        """Extract triplets via LLM.

        Returns empty list on any LLM failure, so callers can fall back
        to rule mode.
        """
        if self._llm is None:
            return []

        try:
            response = self._llm.generate(
                prompt=text,
                system=_LLM_SYSTEM_PROMPT,
                max_tokens=512,
            )
            if not response:
                return []
            return self._parse_llm_response(response)
        except Exception:
            return []

    def _parse_llm_response(self, response: str) -> List[Triplet]:
        """Parse LLM JSON response into Triplet list."""
        # Strip markdown code fences if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove opening fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            if not isinstance(data, list):
                return []
        except json.JSONDecodeError:
            # Try to extract JSON array from within the text
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    if not isinstance(data, list):
                        return []
                except json.JSONDecodeError:
                    return []
            else:
                return []

        results = []
        for item in data:
            if not isinstance(item, dict):
                continue
            subj = str(item.get("s", item.get("subject", ""))).strip()
            pred = str(item.get("p", item.get("predicate", ""))).strip()
            obj = str(item.get("o", item.get("object", ""))).strip()
            if not subj or not pred or not obj:
                continue
            conf = float(item.get("c", item.get("confidence", 0.8)))
            results.append(Triplet(
                subject=subj,
                predicate=pred,
                object=obj,
                confidence=max(0.0, min(1.0, conf)),
                source="llm",
            ))
        return results

    # ── Rule Mode ───────────────────────────────────────────────────────

    # Pattern: (regex, predicate, confidence)
    _CN_PATTERNS = [
        (re.compile(r"(\S+)负责(\S+)"), "负责", 0.8),
        (re.compile(r"(\S+)是(\S+)"), "是", 0.7),
        (re.compile(r"(\S+)的(\S+)"), "拥有", 0.6),
        (re.compile(r"(\S+)在(\S+)"), "位于", 0.6),
        # verb captured in group
        (re.compile(r"(\S+)(喜欢|讨厌|管理|开发|拥有|领导|主管)(\S+)"), None, 0.5),
    ]
    _EN_PATTERNS = [
        (re.compile(r"(\w+)\s+is\s+(\w+)", re.IGNORECASE), "is", 0.7),
        (re.compile(r"(\w+)\s+has\s+(\w+)", re.IGNORECASE), "has", 0.6),
    ]

    def _extract_rule(self, text: str) -> List[Triplet]:
        """Extract triplets using regex patterns only.

        Zero external dependencies; relies solely on Python's re module.
        """
        results: List[Triplet] = []
        seen: set = set()

        # Match Chinese patterns against the full text directly —
        # Chinese patterns use \\S+ which naturally works with CJK text.
        if re.search(r"[\u4e00-\u9fff]", text):
            results.extend(self._match_chinese(text, seen))

        # Match English patterns against English word sequences
        en_segments = re.findall(r"[a-zA-Z]+(?:\s+[a-zA-Z]+)*", text)
        en_text = " ".join(en_segments)
        if en_text:
            results.extend(self._match_english(en_text, seen))

        # If nothing matched, try fallback patterns
        if not results:
            results.extend(self._fallback_match(text, seen))

        return results

    def _match_chinese(self, text: str, seen: set) -> List[Triplet]:
        """Apply Chinese regex patterns."""
        results = []
        for pattern, predicate, confidence in self._CN_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if predicate is None:
                    # Verb is captured in group 1, e.g. (喜欢|讨厌|管理|...)
                    subj, pred, obj = groups[0], groups[1], groups[2]
                else:
                    subj, obj = groups[0], groups[1]
                    pred = predicate

                subj, pred, obj = subj.strip(), pred.strip(), obj.strip()
                # Skip very short or very long entities
                if len(subj) < 1 or len(obj) < 1 or len(subj) > 20 or len(obj) > 20:
                    continue
                key = (subj, pred, obj)
                if key in seen:
                    continue
                seen.add(key)
                results.append(Triplet(
                    subject=subj,
                    predicate=pred,
                    object=obj,
                    confidence=confidence,
                    source="rule",
                ))
        return results

    def _match_english(self, text: str, seen: set) -> List[Triplet]:
        """Apply English regex patterns."""
        results = []
        for pattern, predicate, confidence in self._EN_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                subj, obj = groups[0].strip(), groups[1].strip()
                if len(subj) < 2 or len(obj) < 2:
                    continue
                key = (subj, pred := predicate, obj)
                if key in seen:
                    continue
                seen.add(key)
                results.append(Triplet(
                    subject=subj,
                    predicate=pred,
                    object=obj,
                    confidence=confidence,
                    source="rule",
                ))
        return results

    def _fallback_match(self, text: str, seen: set) -> List[Triplet]:
        """Generic fallback: split on sentences and try simple SVO patterns."""
        results = []
        # Chinese: character-level tri-gram fallback
        cn_sentences = re.split(r"[。！？；\n]", text)
        for sent in cn_sentences:
            sent = sent.strip()
            if len(sent) < 4 or not re.search(r"[\u4e00-\u9fff]", sent):
                continue
            # Try generic pattern: NN V NN
            m = re.search(r"(\S{1,6})(\S{1,4})(\S{1,8})", sent)
            if m:
                subj, pred, obj = m.group(1), m.group(2), m.group(3)
                key = (subj, pred, obj)
                if key in seen:
                    continue
                seen.add(key)
                results.append(Triplet(
                    subject=subj,
                    predicate=pred,
                    object=obj,
                    confidence=0.3,
                    source="rule",
                ))

        # English fallback: subject verb object
        if not results:
            en_pattern = re.compile(r"(\w{2,})\s+(\w{2,})\s+(\w{2,})", re.IGNORECASE)
            for m in en_pattern.finditer(text):
                subj, pred, obj = m.group(1), m.group(2), m.group(3)
                _stopwords = (
                    "the", "and", "for", "with", "from",
                    "that", "this", "then", "when", "where",
                )
                if pred.lower() in _stopwords:
                    continue
                key = (subj, pred, obj)
                if key in seen:
                    continue
                seen.add(key)
                results.append(Triplet(
                    subject=subj,
                    predicate=pred,
                    object=obj,
                    confidence=0.3,
                    source="rule",
                ))

        return results
