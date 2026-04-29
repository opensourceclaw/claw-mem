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
F5 Compression V2 for claw-mem v2.5.0
Improved memory compression with better quality-to-size ratio
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib


class CompressionLevelV2(Enum):
    """Compression levels for F5 V2"""
    LIGHT = 0.3      # 30% compression
    MEDIUM = 0.5     # 50% compression
    AGGRESSIVE = 0.7 # 70% compression
    ULTRA = 0.85     # 85% compression


@dataclass
class CompressionResultV2:
    """Compression result with metadata"""
    original_length: int
    compressed_length: int
    compression_ratio: float
    preserved_content: str
    summary: str
    key_points: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


class F5CompressorV2:
    """F5 Compression V2

    Improvements over V1:
    - Entity-aware compression
    - Topic-based grouping
    - Semantic importance scoring
    - Better summary generation
    """

    # Important entity patterns
    ENTITY_PATTERNS = {
        "person": r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',
        "email": r'\b[\w.-]+@[\w.-]+\.\w+\b',
        "date": r'\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
        "time": r'\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\b',
        "number": r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b',
        "url": r'https?://[^\s]+',
    }

    # Topic keywords
    TOPIC_KEYWORDS = {
        "meeting": ["meeting", "discuss", "schedule", "agenda", "会议", "讨论", "安排"],
        "project": ["project", "task", "milestone", "deadline", "项目", "任务", "里程碑"],
        "decision": ["decided", "agreed", "approved", "decision", "决定", "同意", "批准"],
        "request": ["request", "ask", "need", "want", "would like", "请求", "需要", "想要"],
        "information": ["know", "learn", "remember", "information", "知道", "了解", "记得"],
        "problem": ["issue", "bug", "error", "fix", "problem", "问题", "错误", "修复"],
        "success": ["success", "complete", "finish", "done", "成功", "完成"],
    }

    def __init__(
        self,
        level: CompressionLevelV2 = CompressionLevelV2.MEDIUM,
        preserve_entities: bool = True,
        generate_summary: bool = True
    ):
        self.level = level
        self.preserve_entities = preserve_entities
        self.generate_summary = generate_summary

    def compress(self, content: str) -> CompressionResultV2:
        """Compress content

        Args:
            content: Original content

        Returns:
            CompressionResultV2
        """
        original_length = len(content)

        # Step 1: Extract entities
        entities = self._extract_entities(content)

        # Step 2: Identify topics
        topics = self._identify_topics(content)

        # Step 3: Extract key points
        key_points = self._extract_key_points(content)

        # Step 4: Generate summary
        summary = self._generate_summary(content, key_points, topics) if self.generate_summary else ""

        # Step 5: Compress content
        compressed = self._compress_content(content, key_points, entities)

        compressed_length = len(compressed)
        ratio = 1 - (compressed_length / original_length) if original_length > 0 else 0

        return CompressionResultV2(
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=ratio,
            preserved_content=compressed,
            summary=summary,
            key_points=key_points,
            entities=entities,
            topics=topics
        )

    def _extract_entities(self, text: str) -> List[str]:
        """Extract important entities"""
        entities = []

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            entities.extend(matches)

        # Deduplicate
        return list(set(entities))[:20]  # Limit to 20

    def _identify_topics(self, text: str) -> List[str]:
        """Identify topics in content"""
        text_lower = text.lower()
        topics = []

        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)

        return topics[:5]  # Max 5 topics

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        # Split into sentences
        sentences = re.split(r'[.!?\n]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        # Score each sentence
        scored = []
        for sentence in sentences:
            score = self._score_sentence(sentence)
            scored.append((sentence, score))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Select top sentences based on compression level
        target_count = self._get_target_sentence_count(len(sentences))

        # Get top sentences while maintaining order
        selected = []
        selected_indices = set()
        for sentence, score in scored:
            if len(selected) >= target_count:
                break
            # Find original index
            for i, s in enumerate(sentences):
                if s == sentence and i not in selected_indices:
                    selected.append((sentence, i))
                    selected_indices.add(i)
                    break

        # Sort by original position
        selected.sort(key=lambda x: x[1])
        return [s[0] for s in selected]

    def _score_sentence(self, sentence: str) -> float:
        """Score sentence importance"""
        score = 0
        sentence_lower = sentence.lower()

        # Length factor (prefer medium length)
        length = len(sentence)
        if 20 <= length <= 100:
            score += 2
        elif 100 <= length <= 200:
            score += 1
        elif length < 10:
            score -= 1

        # Important keywords
        important_keywords = [
            'decide', 'agree', 'approve', 'reject', 'important', 'critical',
            'need', 'must', 'should', 'will', 'plan', 'schedule',
            '决定', '同意', '重要', '需要', '必须', '计划',
            'bug', 'fix', 'error', 'issue', 'problem', 'solve',
        ]
        for kw in important_keywords:
            if kw in sentence_lower:
                score += 2

        # Numbers and entities (likely important)
        if re.search(r'\d+', sentence):
            score += 1

        # Question (keep for context)
        if '?' in sentence:
            score += 0.5

        return score

    def _get_target_sentence_count(self, total: int) -> int:
        """Get target number of sentences based on compression level"""
        target_ratio = 1 - self.level.value

        if self.level == CompressionLevelV2.LIGHT:
            return max(int(total * 0.8), 1)
        elif self.level == CompressionLevelV2.MEDIUM:
            return max(int(total * 0.5), 1)
        elif self.level == CompressionLevelV2.AGGRESSIVE:
            return max(int(total * 0.3), 1)
        else:  # ULTRA
            return max(int(total * 0.15), 1)

    def _compress_content(
        self,
        content: str,
        key_points: List[str],
        entities: List[str]
    ) -> str:
        """Compress content while preserving key information"""
        if not key_points:
            # Fallback: truncate
            max_len = int(len(content) * (1 - self.level.value))
            return content[:max_len] + "..." if len(content) > max_len else content

        # Combine key points
        compressed = '. '.join(key_points)

        # Add entity reference if important
        if self.preserve_entities and entities:
            entity_str = f" [Entities: {', '.join(entities[:5])}]"
            compressed += entity_str

        # Ensure punctuation
        if compressed and not compressed.endswith('.'):
            compressed += '.'

        return compressed

    def _generate_summary(
        self,
        content: str,
        key_points: List[str],
        topics: List[str]
    ) -> str:
        """Generate summary"""
        parts = []

        # Topics
        if topics:
            parts.append(f"Topics: {', '.join(topics)}")

        # First key point as anchor
        if key_points:
            first = key_points[0]
            # Truncate to ~50 chars
            if len(first) > 50:
                first = first[:50] + "..."
            parts.append(f"Summary: {first}")

        return ' | '.join(parts)


class UltraCompressor:
    """Ultra compression for extreme space saving

    Uses:
    - Abbreviation rules
    - Core fact extraction
    - Hash-based reference for duplicates
    """

    ABBREVIATIONS = {
        "information": "info",
        "application": "app",
        "example": "eg",
        "number": "num",
        "message": "msg",
        "previous": "prev",
        "following": "fol",
        "including": "incl",
        "without": "w/o",
        "with": "w/",
    }

    def __init__(self):
        self._abbrev_re = re.compile(
            r'\b(' + '|'.join(self.ABBREVIATIONS.keys()) + r')\b',
            re.IGNORECASE
        )

    def compress(self, content: str, max_length: int = 200) -> str:
        """Ultra compress content

        Args:
            content: Original content
            max_length: Maximum output length

        Returns:
            Compressed content
        """
        # Extract core facts
        facts = self._extract_facts(content)

        # Build compressed output
        result = "; ".join(facts)

        # Truncate if needed
        if len(result) > max_length:
            result = result[:max_length-3] + "..."

        return result

    def _extract_facts(self, content: str) -> List[str]:
        """Extract core facts"""
        sentences = re.split(r'[.!?\n]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        facts = []
        for sentence in sentences:
            # Keep sentences with numbers, names, or key verbs
            if re.search(r'\d+', sentence) or self._has_key_verb(sentence):
                # Abbreviate
                compressed = self._abbreviate(sentence)
                facts.append(compressed)

        return facts[:5]  # Max 5 facts

    def _has_key_verb(self, sentence: str) -> bool:
        """Check if sentence has key verbs"""
        verbs = ['decide', 'agree', 'create', 'update', 'delete', 'send', 'receive',
                 '决定', '同意', '创建', '更新', '发送', '接收']
        return any(v in sentence.lower() for v in verbs)

    def _abbreviate(self, text: str) -> str:
        """Apply abbreviations"""
        def replace(match):
            return self.ABBREVIATIONS.get(match.group(0).lower(), match.group(0))

        return self._abbrev_re.sub(replace, text)


# Global instances
_f5_compressor: Optional[F5CompressorV2] = None
_ultra_compressor: Optional[UltraCompressor] = None


def get_f5_compressor(
    level: CompressionLevelV2 = CompressionLevelV2.MEDIUM
) -> F5CompressorV2:
    """Get F5 V2 compressor instance"""
    global _f5_compressor
    if _f5_compressor is None or _f5_compressor.level != level:
        _f5_compressor = F5CompressorV2(level)
    return _f5_compressor


def get_ultra_compressor() -> UltraCompressor:
    """Get ultra compressor instance"""
    global _ultra_compressor
    if _ultra_compressor is None:
        _ultra_compressor = UltraCompressor()
    return _ultra_compressor


def compress_v2(
    content: str,
    level: CompressionLevelV2 = CompressionLevelV2.MEDIUM
) -> CompressionResultV2:
    """Quick compression function"""
    compressor = F5CompressorV2(level)
    return compressor.compress(content)
